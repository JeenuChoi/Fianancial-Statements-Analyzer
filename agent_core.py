import os
import glob
from google import genai
from dart_collector import DartCollector
from dotenv import load_dotenv
import FinanceDataReader as fdr
from datetime import datetime

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class AgentCore:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.dart = DartCollector()
        self.model_id = "gemini-3.1-flash-lite" 

    def load_brain_documents(self):
        """기본 브레인 및 섹터별 브레인 문서 로드"""
        brain = {"common": [], "sectors": {}}
        
        # 공통 가이드 (구조, 크레딧, 희석 등)
        for filepath in glob.glob("analyst_brain/*.md"):
            with open(filepath, 'r', encoding='utf-8') as f:
                brain["common"].append(f.read())
                
        # 섹터별 가이드
        for filepath in glob.glob("analyst_brain/sectors/*.md"):
            filename = os.path.basename(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                brain["sectors"][filename] = f.read()
                
        return brain

    def _determine_sector(self, company_name, parsed_texts):
        """LLM을 사용하여 기업의 섹터를 판단합니다."""
        sample_context = "\n".join(parsed_texts)[:3000] # 개요 위주 추출
        
        sector_files = "\n".join([f"- {f}" for f in os.listdir("analyst_brain/sectors") if f.endswith('.md')])
        
        prompt = f"""
기업명: {company_name}
사업 내용 요약: {sample_context}

다음 섹터 분류 파일 중 이 기업에 가장 잘 맞는 파일명 1개만 정확히 답변하세요.
다른 설명은 제외하고 파일명만 출력하세요.

[후보군]
{sector_files}
"""
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )
        matched_file = response.text.strip()
        print(f"[{company_name}] 섹터 판별 완료: {matched_file}")
        return matched_file
        
    def _get_backtest_data(self, stock_code, year):
        """과거 공시 연도일 경우 익년도 주가 수익률을 계산합니다."""
        target_year = int(year)
        current_year = datetime.now().year
        
        if target_year >= current_year - 1:
             return "" # 너무 최신이거나 미래면 백테스트 불가
             
        try:
             start_date = f"{target_year + 1}-03-01" # 공시 발표 시점 즈음
             end_date = f"{target_year + 1}-12-31"
             df = fdr.DataReader(stock_code, start_date, end_date)
             
             if not df.empty:
                  start_price = df.iloc[0]['Close']
                  end_price = df.iloc[-1]['Close']
                  return_rate = ((end_price - start_price) / start_price) * 100
                  
                  return f"""
[실제 주가 성과 (사후 백테스트 데이터)]
- 기준점: {target_year}년 사업보고서 발표 즈음 ({df.index[0].strftime('%Y-%m-%d')}) 종가 {start_price:,.0f}원
- 목표점: 그 해 연말 ({df.index[-1].strftime('%Y-%m-%d')}) 종가 {end_price:,.0f}원
- 실제 주가 수익률: {return_rate:+.2f}%
"""
        except Exception as e:
             print(f"백테스트 주가 수집 중 오류: {e}")
        return ""

    def analyze_company(self, company_name, year="2025"):
        print(f"==== {company_name} {year}년 공시 자동 분석 에이전트 구동 ==== (백테스트 모드 지원)")
        
        # 1. 고유번호 매핑 및 공시 수집
        corp_info = self.dart.get_corp_info(company_name)
        if not corp_info:
            print("기업 코드를 찾을 수 없습니다.")
            return
            
        corp_code = corp_info["corp_code"]
        stock_code = corp_info["stock_code"]
            
        reports = self.dart.get_recent_reports(corp_code, f"{int(year)-1}0101", pblntf_ty='A')
        if not reports:
            print("최근 정기 공시가 없습니다.")
            return
            
        # 분석 연도(year)가 포함된 보고서만 엄격히 필터링
        target_reports = [r for r in reports if str(year) in r['report_nm']]
        
        if not target_reports:
            print(f"경고: {year}년도 공시를 찾을 수 없습니다. 가장 최신 공시로 대체합니다.")
            target_reports = [reports[0]]
            
        # 1년 전체의 재무와 주석이 담긴 '사업보고서'를 최우선으로 탐색
        annual_reports = [r for r in target_reports if "사업보고서" in r['report_nm']]
        if annual_reports:
             target_reports = [annual_reports[0]]
        else:
             target_reports = [target_reports[0]] # 사업보고서가 없으면 해당 연도의 가장 마지막 분기보고서

        print(f"가장 완벽한 데이터가 담긴 '{target_reports[0]['report_nm']}' 1건 집중 분석 중 (주석 데이터 100% 반영)...")
        
        parsed_texts = []
        for r in target_reports:
            files = self.dart.download_document(r['rcept_no'])
            if files:
                report_text = ""
                # ZIP 내부의 모든 XML(본문 및 연결재무제표 주석 등)을 전부 파싱
                for f in files:
                    if f.endswith('.xml'):
                        report_text += self.dart.extract_text_from_xml(f) + "\n\n"
                parsed_texts.append(f"[{r['report_nm']}]\n{report_text}")
                
        if not parsed_texts:
            print("문서 파싱 실패.")
            return

        # 2. Analyst Brain 로드
        brain = self.load_brain_documents()
        
        # 3. 섹터 식별
        sector_filename = self._determine_sector(company_name, parsed_texts)
        sector_guide = brain["sectors"].get(sector_filename, "")
        
        common_guide = "\n\n".join(brain["common"])
        master_prompt = open("prompt.md", "r", encoding="utf-8").read()
        
        # 주가 백테스트 데이터 수집
        backtest_context = self._get_backtest_data(stock_code, year)
        
        # 4. LLM 딥 분석 요청 (전체 컨텍스트 제공)
        full_context = "\n".join(parsed_texts) 
        
        final_prompt = f"""
{master_prompt}

[애널리스트 공통 뇌 (Common Brain)]
{common_guide}

[특화 섹터 뇌 (Sector Brain): {sector_filename}]
{sector_guide}

{backtest_context}

[실제 기업 데이터 ({company_name})]
이 데이터들을 위 가이드라인에 따라 철저히 분석하라.
{full_context}
"""
        print("LLM 분석 중 (약 30~60초 소요)...")
        response = self.client.models.generate_content(
            model=self.model_id, # Free Tier Rate Limit 방지를 위해 flash 모델 사용
            contents=final_prompt
        )
        
        # 5. 리포트 저장
        output_filename = f"{company_name}_{year}년_최종리포트.md"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"==== 분석 완료! {output_filename}에 저장되었습니다. ====")

if __name__ == "__main__":
    agent = AgentCore()
    print("="*50)
    print("🤖 20년 차 베테랑 공시 분석 에이전트에 오신 것을 환영합니다.")
    print("="*50)
    
    target_company = input("분석할 기업명을 입력하세요 (예: 삼성전자, HMM): ").strip()
    target_year = input("분석할 공시 연도를 입력하세요 (기본값 2025): ").strip()
    if not target_year:
        target_year = "2025"
        
    if target_company:
        agent.analyze_company(target_company, target_year)
    else:
        print("기업명이 입력되지 않아 종료합니다.")
