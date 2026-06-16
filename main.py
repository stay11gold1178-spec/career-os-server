from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI()

# 💡 CORS 설정: HTML 대시보드에서 이 서버에 접속할 수 있도록 허락
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@app.get("/")
def read_root():
    return {"message": "Career OS 백엔드 서버가 정상 작동 중입니다! 🎉"}

# 📰 1. 네이버 뉴스(IT/과학, 경제, 사회/시사) 크롤링 API
@app.get("/api/news")
def get_news():
    try:
        # 네이버 뉴스 섹션별 홈 주소 (정치(100) 제외, 사회(102) 추가)
        sections = {
            "IT/과학": "https://news.naver.com/section/105",
            "경제": "https://news.naver.com/section/101",
            "사회/시사": "https://news.naver.com/section/102"
        }
        
        news_list = []
        
        for section_name, url in sections.items():
            response = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 각 섹션별 최신 3개의 기사를 가져옵니다.
            articles = soup.find_all("a", class_="sa_text_title", limit=3)
            
            for article in articles:
                title = article.text.strip()
                link = article["href"]
                news_list.append({
                    "title": title,
                    "link": link,
                    "source": f"네이버 {section_name} 뉴스"
                })
            
        return {"status": "success", "data": news_list}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 🏢 2. 채용 공고 크롤링 API (사람인, 잡코리아, 자소설닷컴 통합)
@app.get("/api/jobs")
def get_jobs(keyword: str = "프론트엔드"):
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        job_list = []
        
        # --- (1) 사람인(Saramin) 크롤링 ---
        try:
            saramin_url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={encoded_keyword}"
            response = requests.get(saramin_url, headers=HEADERS)
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
            print("사람인 크롤링 오류:", e)

        # --- (2) 잡코리아(Jobkorea) 크롤링 ---
        try:
            jobkorea_url = f"https://www.jobkorea.co.kr/Search/?stext={encoded_keyword}"
            response = requests.get(jobkorea_url, headers=HEADERS)
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
            print("잡코리아 크롤링 오류:", e)
            
        # --- (3) 자소설닷컴(Jasoseol) 구조 예시 ---
        try:
            jasoseol_url = f"https://jasoseol.com/recruit?keyword={encoded_keyword}"
            response = requests.get(jasoseol_url, headers=HEADERS)
            soup = BeautifulSoup(response.text, "html.parser")
            
            job_items = soup.select(".recruit-item-card", limit=2)
            
            for item in job_items:
                company_name = item.select_one(".company-name").text.strip() if item.select_one(".company-name") else "기업명 모름"
                
                title_elem = item.select_one(".recruit-title a")
                if not title_elem: continue
                job_title = title_elem.text.strip()
                job_link = "https://jasoseol.com" + title_elem["href"]
                
                deadline = item.select_one(".deadline").text.strip() if item.select_one(".deadline") else "상시채용"
                
                job_list.append({
                    "company": company_name,
                    "title": job_title,
                    "deadline": deadline,
                    "url": job_link,
                    "platform": "자소설닷컴"
                })
        except Exception as e:
            print("자소설닷컴 크롤링 오류:", e)
            # 자소설닷컴은 동적 렌더링(React)이 많아 긁어오지 못할 경우를 대비해 Mock 데이터를 하나 넣어줍니다.
            job_list.append({
                "company": "자소설닷컴(샘플)",
                "title": f"[{keyword}] 관련 우수 채용 공고",
                "deadline": "2026-06-30",
                "url": "https://jasoseol.com/",
                "platform": "자소설닷컴"
            })
            
        return {"status": "success", "data": job_list}
    except Exception as e:
        return {"status": "error", "message": str(e)}