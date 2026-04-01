import feedparser
import smtplib
import os
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# ==========================================
# ⚙️ 봇 설정 변수
# ==========================================
SEARCH_TOPIC = "인공지능 AI 최신 기술"        # 검색할 주제 (구글 뉴스 검색 최적화)
EXPERT_ROLE = "수석 AI 기술 분석 전문가"     # 제미나이 역할
NEWS_COUNT = 10                          # 가져올 뉴스 개수
SUMMARY_SENTENCE_COUNT = 3               # 요약할 문장 수
# ==========================================

def get_news_data():
    encoded_topic = urllib.parse.quote(SEARCH_TOPIC)
    rss_url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    news_text_for_gemini = ""
    
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
    
    prompt = f"""
    너는 {EXPERT_ROLE}야. 아래의 최신 '{SEARCH_TOPIC}' 관련 뉴스 헤드라인 {NEWS_COUNT}개를 읽고, 
    오늘의 주요 트렌드를 일반인이 이해하기 쉽게 딱 {SUMMARY_SENTENCE_COUNT}문장으로 핵심만 요약해줘.
    
    [가독성 규칙]
    1. 이메일 본문에 들어갈 내용이므로 HTML 태그(<strong> 등)를 사용해줘. (마크다운 기호 금지)
    2. 글이 답답해 보이지 않도록, **각 문장이 끝날 때마다 반드시 줄바꿈 태그(<br><br>)를 두 번씩 넣어서** 문장과 문장 사이를 넉넉하게 띄워줘.
    
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
    # 이메일 제목을 조금 더 전문가 리포트 느낌으로 다듬었습니다
    msg['Subject'] = f"🤖 [AI Expert 브리핑] 오늘의 인공지능 트렌드 분석"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    news_list_html = ""
    for item in news_items:
        news_list_html += f"""
        <li style='margin-bottom: 15px; line-height: 1.6;'>
            <a href='{item['link']}' style='color: #1a73e8; text-decoration: none; font-weight: bold; font-size: 15px;'>
                {item['title']}
            </a>
        </li>
        """

    html_body = f"""
    <html>
    <body style='font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif; color: #333; line-height: 1.8; word-break: keep-all;'>
        <div style='max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 25px; border-radius: 12px;'>
            <h2 style='color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 12px; margin-top: 0;'>
                💡 오늘의 AI 트렌드 인사이트
            </h2>
            
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; line-height: 2.0; font-size: 16px;'>
                {summary_html}
            </div>
            
            <h3 style='color: #444; margin-bottom: 15px;'>🔗 실시간 AI 주요 뉴스 Top {NEWS_COUNT}</h3>
            <ul style='list-style: none; padding-left: 0;'>
                {news_list_html}
            </ul>
            
            <hr style='border: 0; border-top: 1px solid #eee; margin: 30px 0;'>
            <p style='font-size: 12px; color: #999; text-align: center; line-height: 1.5;'>
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
    
    print(f"제미나이 요약 생성 중... (목표: {SUMMARY_SENTENCE_COUNT}문장)")
    summary = ask_gemini(text_for_ai)
    
    print("이메일 발송 중...")
    send_email(items, summary)
