import feedparser
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

def get_ai_news_data():
    # 1. 구글 뉴스 RSS에서 최신 AI 뉴스 10개 수집
    rss_url = "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    news_items = []
    news_text_for_gemini = ""
    
    for entry in feed.entries[:10]:
        # 메일 하단 리스트용 데이터
        news_items.append({
            "title": entry.title,
            "link": entry.link
        })
        # 제미나이 분석용 텍스트
        news_text_for_gemini += f"- {entry.title}\n"
    
    return news_items, news_text_for_gemini

def ask_gemini(news_text):
    # 2. 제미나이에게 요약 요청
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=gemini_api_key)
    
    prompt = f"""
    너는 IT 전문 뉴스 에디터야. 아래의 최신 AI 뉴스 헤드라인들을 읽고, 
    오늘의 주요 트렌드를 일반인이 이해하기 쉽게 5문장 이내로 요약해줘.
    
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
    # 3. 이메일 구성 및 발송
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_email = os.environ.get('RECEIVER_EMAIL')

    msg = MIMEMultipart()
    msg['Subject'] = "🤖 오늘의 AI 트렌드 & 주요 뉴스 리포트"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # 뉴스 리스트를 HTML <li> 태그로 변환
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
            <h2 style='color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;'>✨ 오늘의 AI 트렌드 요약</h2>
            <div style='background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
                {summary_html}
            </div>
            
            <h3 style='color: #444;'>🔗 주요 뉴스 Top 10</h3>
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
    print("뉴스 수집 및 분석 시작...")
    items, text_for_ai = get_ai_news_data()
    
    print("제미나이 요약 생성 중...")
    summary = ask_gemini(text_for_ai)
    
    print("이메일 발송 중...")
    send_email(items, summary)
