import feedparser
import smtplib
import os
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_ai_news_titles():
    # 1. 구글 뉴스 RSS에서 AI 관련 뉴스 긁어오기
    rss_url = "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    titles = []
    for entry in feed.entries[:5]: # 최신 뉴스 5개 추출
        titles.append(f"- {entry.title} ({entry.link})")
    
    return "\n".join(titles)

def ask_gemini(news_text):
    # 2. 제미나이 API 설정
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=gemini_api_key)
    
    # 사용할 모델 선택 (최신 Flash 모델이 빠르고 가성비가 좋습니다)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 제미나이에게 내릴 프롬프트(명령)
    prompt = f"""
    너는 최고의 AI 트렌드 분석가야. 아래 오늘자 AI 뉴스 헤드라인 5개를 읽고, 
    오늘의 AI 기술 트렌드를 3~4문장으로 핵심만 요약해줘.
    
    그리고 이메일 본문으로 쓸 거니까, 반드시 HTML 태그(<br>, <strong>, <ul>, <li> 등)를 
    사용해서 깔끔하고 예쁘게 꾸며서 답변해줘. 마크다운(```html) 기호는 빼고 순수 HTML만 출력해.
    
    [오늘의 뉴스]
    {news_text}
    """
    
    response = model.generate_content(prompt)
    return response.text

def send_email(gemini_html_content):
    # 3. 이메일 발송 세팅
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    receiver_email = os.environ.get('RECEIVER_EMAIL')

    msg = MIMEMultipart()
    msg['Subject'] = "🤖 [Gemini 분석] 오늘의 AI 트렌드 리포트"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # 제미나이가 만들어준 HTML을 메일 본문에 그대로 삽입
    html_body = f"""
    <html>
    <body style='font-family: Arial, sans-serif; line-height: 1.6;'>
        <h2 style='color:#1a73e8;'>✨ Gemini가 분석한 오늘의 AI 트렌드</h2>
        <div style='background-color:#f8f9fa; padding:15px; border-radius:8px;'>
            {gemini_html_content}
        </div>
        <br>
        <p style='color:#999; font-size:11px;'>본 메일은 GitHub Actions와 Gemini API를 통해 자동 발송되었습니다.</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        # Gmail 서버 연결 및 발송
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("✅ 이메일 발송 완료!")
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")

if __name__ == "__main__":
    print("뉴스 수집 중...")
    news_data = get_ai_news_titles()
    
    print("제미나이 분석 중...")
    gemini_insight = ask_gemini(news_data)
    
    print("이메일 전송 중...")
    send_email(gemini_insight)
