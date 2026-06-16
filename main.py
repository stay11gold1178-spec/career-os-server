from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 💡 핵심 해결책: 로봇 차단을 뚫기 위한 "완벽한 사람 위장 신분증"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"  # 구글 검색을 타고 들어온 것처럼 위장!
}

@app.get("/")
def read_root():
    return {"message": "Career OS 백엔드 서버가 정상 작동 중입니다! 🎉"}

# 📰 1. 네이버 뉴스 (IT/과학, 경제, 사회/시사)
@app.get("/api/news")
def get_news():
    try:
        sections = {
            "IT/과학": "https://news.naver.com/section/105",
            "경제": "https://news.naver.com/section/101",
            "사회/시사": "https://news.naver.com/section/102"
        }
        news_list = []
        for section_name, url in sections.items():
            response = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("a", class_="sa_text_title", limit=3)
            for article in articles:
                news_list.append({
                    "title": article.text.strip(),
                    "link": article["href"],
                    "source": f"네이버 {section_name} 뉴스"
                })
        return {"status": "success", "data": news_list}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 🏢 2. 사람인 & 잡코리아 공고 크롤링
@app.get("/api/jobs")
def get_jobs(keyword: str = "프론트엔드"):
    encoded_keyword = urllib.parse.quote(keyword)
    job_list = []
    
    # --- (1) 사람인(Saramin) 크롤링 (차단 우회) ---
    try:
        # 사람인 전용 헤더 추가 (직접 접속한 것처럼)
        saramin_headers = HEADERS.copy()
        saramin_headers["Referer"] = "https://www.saramin.co.kr/"
        
        saramin_url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={encoded_keyword}"
        response = requests.get(saramin_url, headers=saramin_headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        
        job_items = soup.select(".item_recruit", limit=3) 
        for item in job_items:
            corp_elem = item.select_one(".corp_name a")
            company_name = corp_elem.text.strip() if corp_elem else "기업명 모름"
            
            title_elem = item.select_one(".job_tit a")
            if not title_elem: continue
            job_title = title_elem["title"].strip()
            job_link = "https://www.saramin.co.kr" + title_elem["href"]
                
            date_elem = item.select_one(".job_date .date")
            deadline = date_elem.text.strip() if date_elem else "상시채용"

            job_list.append({
                "company": company_name,
                "title": job_title,
                "deadline": deadline,
                "url": job_link,
                "platform": "사람인"
            })
    except Exception as e:
        print(f"사람인 차단됨: {e}")

    # --- (2) 잡코리아(Jobkorea) 크롤링 (차단 우회) ---
    try:
        jobkorea_headers = HEADERS.copy()
        jobkorea_headers["Referer"] = "https://www.jobkorea.co.kr/"
        
        jobkorea_url = f"https://www.jobkorea.co.kr/Search/?stext={encoded_keyword}"
        response = requests.get(jobkorea_url, headers=jobkorea_headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        
        job_items = soup.select(".list-default .list-post", limit=3)
        for item in job_items:
            corp_elem = item.select_one(".corp-name a")
            company_name = corp_elem.text.strip() if corp_elem else "기업명 모름"
            
            title_elem = item.select_one(".post-list-info a")
            if not title_elem: continue
            job_title = title_elem.text.strip()
            job_link = "https://www.jobkorea.co.kr" + title_elem["href"]
            
            date_elem = item.select_one(".option .date")
            deadline = date_elem.text.strip() if date_elem else "상시채용"
            
            job_list.append({
                "company": company_name,
                "title": job_title,
                "deadline": deadline,
                "url": job_link,
                "platform": "잡코리아"
            })
    except Exception as e:
        print(f"잡코리아 차단됨: {e}")

    # 자소설닷컴은 특수한 화면 렌더링 방식(React/SPA)을 써서 파이썬의 단순 Requests로는 데이터를 숨겨버리기 때문에
    # 크롤러가 사이트를 망가뜨렸다고 오해하지 않도록, 검색어에 맞춘 임시 링크를 제공합니다.
    job_list.append({
        "company": "자소설닷컴(공식)",
        "title": f"[{keyword}] 실시간 채용달력 보러가기",
        "deadline": "상시확인",
        "url": f"https://jasoseol.com/recruit?keyword={encoded_keyword}",
        "platform": "자소설닷컴"
    })
        
    return {"status": "success", "data": job_list}
