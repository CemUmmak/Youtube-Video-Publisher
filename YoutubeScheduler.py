import os
import sys
import re
import random
import pandas as pd
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def print_progress(current, total, filename):
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = '█' * filled + '-' * (bar_length - filled)
    percent = (current / total) * 100
    sys.stdout.write(f"\r📦 {filename:<30} |{bar}| {current}/{total} ({percent:.1f}%)")
    sys.stdout.flush()


def youtube_authenticate():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    credentials = flow.run_local_server()
    return build("youtube", "v3", credentials=credentials)

def extract_number(filename):
     match = re.search(r'\d+', filename)
     return int(match.group()) if match else float('inf')

def upload_scheduled_video(file_path, title, description, tags, publish_time, youtube):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_time,
            "selfDeclaredMadeForKids": False
        }
    }

    media_file = MediaFileUpload(file_path)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media_file
    )
    response = request.execute()


def generate_and_upload(start_date, videos_per_day, time_slots,
                        video_folder, titles_csv, descriptions_csv, hashtags_csv,
                        total_video_limit):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    titles = pd.read_csv(titles_csv, header=None)[0].tolist()
    descriptions = pd.read_csv(descriptions_csv, header=None)[0].tolist()
    hashtags = pd.read_csv(hashtags_csv, header=None)[0].tolist()



    video_files = sorted([
        f for f in os.listdir(video_folder)
        if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv")) and not f.startswith("P_")
    ], key=extract_number)

    video_files = video_files[:total_video_limit]
    total_files = len(video_files)
    schedule_data = []
    youtube = youtube_authenticate()

    for i, video_file in enumerate(video_files, start=1):
        day_offset = (i - 1) // videos_per_day
        slot_index = (i - 1) % videos_per_day

        publish_date = start_date + timedelta(days=day_offset)
        publish_time = datetime.strptime(time_slots[slot_index], "%H:%M").time()
        publish_datetime = datetime.combine(publish_date, publish_time)
        publish_utc = publish_datetime - timedelta(hours=3)

        title = random.choice(titles)
        description = random.choice(descriptions)
        hashtag = random.choice(hashtags)

        original_path = os.path.join(video_folder, video_file)
        new_filename = "P_" + video_file
        new_path = os.path.join(video_folder, new_filename)
        os.rename(original_path, new_path)

        schedule_data.append({
            "video_file": new_path,
            "title": title,
            "description": f"{description} {hashtag}",
            "tags": [tag.strip("#") for tag in hashtag.split()],
            "publish_at": publish_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        })

        print_progress(i, total_files, new_filename)

        # Gerçek YouTube yüklemesi
        upload_scheduled_video(
            file_path=new_path,
            title=title,
            description=f"{description} {hashtag}",
            tags=[tag.strip("#") for tag in hashtag.split()],
            publish_time=publish_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            youtube=youtube
        )

    df = pd.DataFrame(schedule_data)
    print(df)
    print(f"\n📦 Planlama ve yükleme tamamlandı.")

