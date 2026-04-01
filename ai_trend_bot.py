import feedparser
import smtplib
import os
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# ==========================================
# ⚙️ 봇 설정 변수 (앞으로는 여기만 수정하세요!)
# ==========================================
SEARCH_TOPIC = "AI 최신 뉴스"             # 검색할 주제 (예: "미국 금리 인하", "테슬라 주가")
EXPERT_ROLE = "AI 분석 전문 애널리스트" # 제미나이 역할 (예: "거시경제 전문가", "월가 주식 트레이더")
NEWS_COUNT = 10                          # 가져올 뉴스 개수
# ==========================================

def get_news_data():
    # 1. 설정한 주제를 인터넷 주소용으로 변환
    encoded_topic = urllib.parse.quote(SEARCH_TOPIC)
    rss_url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    news_text_for_gemini = ""
    
    # 설정한 개수(NEWS_COUNT)만큼만 뉴스 가져오기
    for entry in feed.entries[:NEWS_COUNT]:
        news_items.append({
            "title": entry.title,
            "link": entry.link
        })
        news_text_for_gemini += f"- {entry.title}\n"
    
    return news_items, news_text_for_gemini

def ask_gemini(news_text):
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=gemini_api_key)
    
    # 2. 프롬프트에 설정 변수들(역할, 주제, 개수)을 자동으로 쏙쏙 집어넣기
    prompt = f"""
    너는 {EXPERT_ROLE}야. 아래의 최신 '{SEARCH_TOPIC}' 관련 뉴스 헤드라인 {NEWS_COUNT}개를 읽고, 
    오늘의 주요 트렌드를 일반인이 이해하기 쉽게 3~4문장으로 핵심만 요약해줘.
    
    이메일 본문에 들어갈 내용이므로 HTML 태그(<strong>, <br> 등)를 
    적절히 섞어서 가독성 좋게 작성해줘. (마크다운 형식 금지)
    
    [뉴스 헤드라인]
    {news_text}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def send_email(news_items, summary_html):
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_email = os.environ.get('RECEIVER_EMAIL')

    msg = MIMEMultipart()
    # 3. 이메일 제목에도 주제(SEARCH_TOPIC)가 자동으로 들어가도록 설정
    msg['Subject'] = f"🤖 [Gemini 리포트] 오늘의 {SEARCH_TOPIC} 트렌드 요약"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    news_list_html = ""
    for item in news_items:
        news_list_html += f"""
        <li style='margin-bottom: 10px;'>
            <a href='{item['link']}' style='color: #1a73e8; text-decoration: none; font-weight: bold;'>
                {item['title']}
            </a>
        </li>
        """

    html_body = f"""
    <html>
    <body style='font-family: Arial, sans-serif; color: #333; line-height: 1.6;'>
        <div style='max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;'>
            <h2 style='color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;'>
                ✨ 오늘의 {SEARCH_TOPIC} 트렌드
            </h2>
            <div style='background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
                {summary_html}
            </div>
            
            <h3 style='color: #444;'>🔗 주요 뉴스 Top {NEWS_COUNT}</h3>
            <ul style='list-style: none; padding-left: 0;'>
                {news_list_html}
            </ul>
            
            <hr style='border: 0; border-top: 1px solid #eee; margin: 20px 0;'>
            <p style='font-size: 11px; color: #999; text-align: center;'>
                본 리포트는 GitHub Actions와 Gemini 2.5 Flash 모델을 사용하여 자동으로 생성되었습니다.
            </p>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("✅ 이메일 발송 완료!")
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")

if __name__ == "__main__":
    print(f"[{SEARCH_TOPIC}] 뉴스 수집 및 분석 시작...")
    items, text_for_ai = get_news_data()
    
    print("제미나이 요약 생성 중...")
    summary = ask_gemini(text_for_ai)
    
    print("이메일 발송 중...")
    send_email(items, summary)
