#!/usr/bin/env python3
"""
Outdoor Boys Knowledge Base Builder

This script scrapes the Outdoor Boys YouTube channel to build
a knowledge base for the chat interface.

Usage:
    python scraper/main.py --api-key YOUR_YOUTUBE_API_KEY --anthropic-key YOUR_ANTHROPIC_KEY

Requirements:
    pip install google-api-python-client youtube-transcript-api anthropic sentence-transformers
"""

import argparse
import json
import os
import time
from datetime import datetime
from typing import Optional
import hashlib

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import anthropic

# Outdoor Boys Channel ID (find this from the channel URL)
CHANNEL_ID = "UCXCbmqLdPscHPhFL7gqPOhQ"  # Update with actual Outdoor Boys channel ID

# Category mapping based on playlist titles
CATEGORY_KEYWORDS = {
    'winter_survival': ['winter', 'cold', 'snow', 'ice', 'freeze', 'survival', 'shelter'],
    'building': ['build', 'cabin', 'construction', 'sauna', 'house', 'shed'],
    'fishing': ['fish', 'fishing', 'catch', 'salmon', 'trout', 'halibut'],
    'camping': ['camp', 'camping', 'tent', 'outdoor'],
    'cooking': ['cook', 'recipe', 'food', 'meal', 'eat'],
    'gear': ['gear', 'equipment', 'review', 'tool'],
    'alaska': ['alaska', 'wild', 'wilderness', 'adventure'],
    'family': ['family', 'kids', 'boys'],
}


class OutdoorBoysScraper:
    def __init__(self, youtube_api_key: str, anthropic_api_key: Optional[str] = None):
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        self.anthropic = anthropic.Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None
        self.rate_limit_delay = 0.5  # seconds between API calls
        
    def _infer_category(self, title: str, description: str = '') -> str:
        """Infer category from title and description keywords."""
        text = (title + ' ' + description).lower()
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category
        return 'general'
    
    def get_channel_playlists(self) -> list[dict]:
        """Fetch all playlists from the channel."""
        playlists = []
        request = self.youtube.playlists().list(
            part='snippet,contentDetails',
            channelId=CHANNEL_ID,
            maxResults=50
        )
        
        while request:
            response = request.execute()
            for item in response.get('items', []):
                playlists.append({
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'video_count': item['contentDetails']['itemCount'],
                    'category': self._infer_category(item['snippet']['title'])
                })
            request = self.youtube.playlists().list_next(request, response)
            time.sleep(self.rate_limit_delay)
        
        return playlists
    
    def get_playlist_videos(self, playlist_id: str) -> list[dict]:
        """Get all videos from a specific playlist."""
        videos = []
        request = self.youtube.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=playlist_id,
            maxResults=50
        )
        
        while request:
            response = request.execute()
            for item in response.get('items', []):
                videos.append({
                    'video_id': item['contentDetails']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'published_at': item['snippet']['publishedAt'],
                    'playlist_id': playlist_id,
                })
            request = self.youtube.playlistItems().list_next(request, response)
            time.sleep(self.rate_limit_delay)
        
        return videos
    
    def get_all_channel_videos(self) -> list[dict]:
        """Get all videos from the channel's uploads playlist."""
        # First get the uploads playlist ID
        channel_response = self.youtube.channels().list(
            part='contentDetails',
            id=CHANNEL_ID
        ).execute()
        
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        return self.get_playlist_videos(uploads_playlist_id)
    
    def get_transcript(self, video_id: str) -> Optional[dict]:
        """Get transcript for a video."""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = ' '.join([t['text'] for t in transcript_list])
            return {
                'video_id': video_id,
                'segments': transcript_list,
                'full_text': full_text
            }
        except Exception as e:
            print(f"  Could not get transcript for {video_id}: {e}")
            return None
    
    def extract_facts_with_llm(self, video: dict, transcript: str) -> dict:
        """Use Claude to extract structured facts from transcript."""
        if not self.anthropic:
            return {'facts': [], 'jokes': [], 'businesses': [], 'recipes': []}
        
        prompt = f"""Analyze this Outdoor Boys YouTube video transcript and extract structured information.

Video Title: {video['title']}
Video Description: {video['description'][:500]}

Transcript (first 12000 chars):
{transcript[:12000]}

Extract the following into valid JSON:
{{
    "survival_tips": ["specific actionable tip 1", "tip 2"],
    "building_techniques": ["technique with detail"],
    "life_lessons": ["wisdom/philosophy shared"],
    "dad_jokes": ["any jokes Zach tells"],
    "gear_recommendations": [{{"name": "item name", "use": "what it's for", "recommendation": "why recommended"}}],
    "recipes": [{{"name": "dish name", "ingredients": ["ing1"], "steps": ["step1"], "cooking_method": "campfire|grill|indoor"}}],
    "businesses_mentioned": [{{"name": "business name", "type": "charter|restaurant|store|lodge|guide", "location": "city, state", "contact": "if mentioned"}}],
    "fishing_tips": ["specific fishing advice"]
}}

Only include items that are clearly mentioned in the transcript. Be specific and detailed.
Return ONLY valid JSON, no other text."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            return json.loads(response.content[0].text)
        except Exception as e:
            print(f"  LLM extraction failed: {e}")
            return {'facts': [], 'jokes': [], 'businesses': [], 'recipes': []}
    
    def extract_businesses_from_description(self, description: str) -> list[dict]:
        """Extract business mentions from video description."""
        if not self.anthropic:
            return []
        
        prompt = f"""Extract any businesses, services, or locations mentioned in this YouTube video description:

{description}

Look for:
- Charter services (fishing, hunting guides)
- Restaurants/lodges
- Equipment stores/brands with links
- Specific locations with contact info

Return as JSON array:
[{{"name": "", "type": "charter|restaurant|store|lodge|guide|other", "location": "", "website": "", "contact": ""}}]

Return ONLY valid JSON array, no other text. Return [] if no businesses found."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return json.loads(response.content[0].text)
        except:
            return []


def generate_id(content: str) -> str:
    """Generate a unique ID for a piece of content."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def build_knowledge_base(scraper: OutdoorBoysScraper, output_dir: str, max_videos: int = 10):
    """Build the complete knowledge base."""
    print("🏔️ Building Outdoor Boys Knowledge Base\n")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Collect all facts, businesses, jokes, recipes
    all_facts = []
    all_businesses = []
    all_jokes = []
    all_recipes = []
    categories = {}
    
    # Get playlists for categories
    print("📋 Fetching playlists...")
    playlists = scraper.get_channel_playlists()
    for p in playlists:
        categories[p['id']] = {
            'id': p['id'],
            'name': p['title'],
            'description': p['description'],
            'playlistId': p['id'],
            'category': p['category'],
            'factCount': 0
        }
    print(f"   Found {len(playlists)} playlists\n")
    
    # Get videos
    print("🎬 Fetching videos...")
    videos = scraper.get_all_channel_videos()[:max_videos]  # Limit for demo
    print(f"   Processing {len(videos)} videos\n")
    
    for i, video in enumerate(videos):
        print(f"📹 [{i+1}/{len(videos)}] {video['title'][:50]}...")
        
        # Get transcript
        transcript_data = scraper.get_transcript(video['video_id'])
        if not transcript_data:
            continue
        
        # Extract facts with LLM
        extracted = scraper.extract_facts_with_llm(video, transcript_data['full_text'])
        category = scraper._infer_category(video['title'], video['description'])
        
        # Process survival tips
        for tip in extracted.get('survival_tips', []):
            all_facts.append({
                'id': generate_id(tip),
                'type': 'survival_tip',
                'content': tip,
                'category': category,
                'videoId': video['video_id'],
                'videoTitle': video['title'],
                'tags': ['survival', category]
            })
        
        # Process building techniques
        for tech in extracted.get('building_techniques', []):
            all_facts.append({
                'id': generate_id(tech),
                'type': 'building_technique',
                'content': tech,
                'category': 'building',
                'videoId': video['video_id'],
                'videoTitle': video['title'],
                'tags': ['building', 'construction']
            })
        
        # Process life lessons
        for lesson in extracted.get('life_lessons', []):
            all_facts.append({
                'id': generate_id(lesson),
                'type': 'life_lesson',
                'content': lesson,
                'category': 'life_lessons',
                'videoId': video['video_id'],
                'videoTitle': video['title'],
                'tags': ['wisdom', 'philosophy']
            })
        
        # Process fishing tips
        for tip in extracted.get('fishing_tips', []):
            all_facts.append({
                'id': generate_id(tip),
                'type': 'fishing_tip',
                'content': tip,
                'category': 'fishing',
                'videoId': video['video_id'],
                'videoTitle': video['title'],
                'tags': ['fishing']
            })
        
        # Process gear
        for gear in extracted.get('gear_recommendations', []):
            if isinstance(gear, dict):
                content = f"{gear.get('name', 'Unknown')}: {gear.get('use', '')} - {gear.get('recommendation', '')}"
            else:
                content = str(gear)
            all_facts.append({
                'id': generate_id(content),
                'type': 'gear',
                'content': content,
                'category': 'gear',
                'videoId': video['video_id'],
                'videoTitle': video['title'],
                'tags': ['gear', 'equipment']
            })
        
        # Process dad jokes
        for joke in extracted.get('dad_jokes', []):
            all_jokes.append({
                'id': generate_id(joke),
                'punchline': joke,
                'context': video['title'],
                'videoId': video['video_id'],
                'videoTitle': video['title']
            })
        
        # Process recipes
        for recipe in extracted.get('recipes', []):
            if isinstance(recipe, dict):
                all_recipes.append({
                    'id': generate_id(recipe.get('name', '')),
                    'name': recipe.get('name', 'Unknown Recipe'),
                    'description': f"From {video['title']}",
                    'ingredients': recipe.get('ingredients', []),
                    'steps': recipe.get('steps', []),
                    'cookingMethod': recipe.get('cooking_method', 'campfire'),
                    'videoId': video['video_id'],
                    'videoTitle': video['title']
                })
        
        # Process businesses from extraction
        for biz in extracted.get('businesses_mentioned', []):
            if isinstance(biz, dict) and biz.get('name'):
                all_businesses.append({
                    'id': generate_id(biz.get('name', '')),
                    'name': biz.get('name', ''),
                    'type': biz.get('type', 'other'),
                    'location': biz.get('location', ''),
                    'contact': biz.get('contact', ''),
                    'website': biz.get('website', ''),
                    'videoReferences': [{'videoId': video['video_id'], 'videoTitle': video['title']}],
                    'description': f"Mentioned in {video['title']}"
                })
        
        # Also extract businesses from description
        desc_businesses = scraper.extract_businesses_from_description(video['description'])
        for biz in desc_businesses:
            if isinstance(biz, dict) and biz.get('name'):
                all_businesses.append({
                    'id': generate_id(biz.get('name', '')),
                    'name': biz.get('name', ''),
                    'type': biz.get('type', 'other'),
                    'location': biz.get('location', ''),
                    'contact': biz.get('contact', ''),
                    'website': biz.get('website', ''),
                    'videoReferences': [{'videoId': video['video_id'], 'videoTitle': video['title']}],
                    'description': f"From video description: {video['title']}"
                })
        
        time.sleep(0.5)  # Rate limiting
    
    # Note: In production, you'd compute embeddings here
    # For now, embeddings will be computed client-side or with a separate script
    print("\n⚠️  Note: Embeddings not computed. Run compute_embeddings.py separately.\n")
    
    # Save outputs
    print("💾 Saving knowledge base files...")
    
    # Metadata
    metadata = {
        'lastUpdated': datetime.now().isoformat(),
        'totalVideos': len(videos),
        'totalFacts': len(all_facts),
        'version': '1.0.0',
        'channelName': 'Outdoor Boys'
    }
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Categories
    with open(os.path.join(output_dir, 'categories.json'), 'w') as f:
        json.dump(list(categories.values()), f, indent=2)
    
    # Facts (without embeddings for now)
    with open(os.path.join(output_dir, 'facts.json'), 'w') as f:
        json.dump(all_facts, f, indent=2)
    
    # Businesses
    with open(os.path.join(output_dir, 'businesses.json'), 'w') as f:
        json.dump(all_businesses, f, indent=2)
    
    # Jokes
    with open(os.path.join(output_dir, 'jokes.json'), 'w') as f:
        json.dump(all_jokes, f, indent=2)
    
    # Recipes
    with open(os.path.join(output_dir, 'recipes.json'), 'w') as f:
        json.dump(all_recipes, f, indent=2)
    
    print(f"""
✅ Knowledge base built successfully!

📊 Statistics:
   - Facts: {len(all_facts)}
   - Businesses: {len(all_businesses)}
   - Dad Jokes: {len(all_jokes)}
   - Recipes: {len(all_recipes)}
   - Categories: {len(categories)}

📁 Files saved to: {output_dir}/
   - metadata.json
   - categories.json
   - facts.json
   - businesses.json
   - jokes.json
   - recipes.json

🔜 Next steps:
   1. Run compute_embeddings.py to add vector embeddings
   2. Copy files to frontend/public/knowledge-base/
   3. Build and deploy the frontend
""")


def main():
    parser = argparse.ArgumentParser(description='Build Outdoor Boys Knowledge Base')
    parser.add_argument('--api-key', required=True, help='YouTube Data API key')
    parser.add_argument('--anthropic-key', help='Anthropic API key for fact extraction')
    parser.add_argument('--output', default='./knowledge-base', help='Output directory')
    parser.add_argument('--max-videos', type=int, default=10, help='Max videos to process')
    
    args = parser.parse_args()
    
    scraper = OutdoorBoysScraper(args.api_key, args.anthropic_key)
    build_knowledge_base(scraper, args.output, args.max_videos)


if __name__ == '__main__':
    main()
