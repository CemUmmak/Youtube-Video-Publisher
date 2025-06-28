from YoutubeScheduler import generate_and_upload

generate_and_upload(
    start_date="2025-06-30",
    videos_per_day=3,
    time_slots=["11:00", "16:00", "21:00"],
    video_folder="Videos",
    titles_csv="titles.csv",
    descriptions_csv="descriptions.csv",
    hashtags_csv="hashtags.csv",
    total_video_limit=90
)