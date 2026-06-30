import os
import io
import zipfile
import json
import xml.etree.ElementTree as ET
import requests
from dotenv import load_dotenv

load_dotenv()
DART_API_KEY = os.getenv("DART_API_KEY")

if not DART_API_KEY:
    raise ValueError("DART_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

class DartCollector:
    def __init__(self):
        self.api_key = DART_API_KEY
        self.base_url = "https://opendart.fss.or.kr/api"
        self.corp_codes = self._load_corp_codes()

    def _load_corp_codes(self):
        """DART 고유번호 ZIP 파일을 다운로드하여 파싱합니다."""
        print("고유번호 목록을 다운로드하는 중입니다...")
        url = f"{self.base_url}/corpCode.xml"
        params = {"crtfc_key": self.api_key}
        res = requests.get(url, params=params, timeout=30)
        
        if res.status_code != 200:
            raise Exception("고유번호 다운로드 실패")
            
        with zipfile.ZipFile(io.BytesIO(res.content)) as z:
            xml_data = z.read("CORPCODE.xml")
            
        root = ET.fromstring(xml_data)
        corp_codes = {}
        for list_tag in root.findall('list'):
            corp_name = list_tag.find('corp_name').text
            corp_code = list_tag.find('corp_code').text
            stock_code = list_tag.find('stock_code').text
            
            if stock_code and stock_code.strip() != "":
                corp_codes[corp_name] = {
                    "corp_code": corp_code,
                    "stock_code": stock_code.strip()
                }
        
        print(f"총 {len(corp_codes)}개의 상장사 고유번호를 로드했습니다.")
        return corp_codes

    def get_corp_info(self, corp_name):
        return self.corp_codes.get(corp_name)

    def get_recent_reports(self, corp_code, bgn_de, pblntf_ty='A'):
        """
        정기공시 목록 조회
        pblntf_ty='A' (정기공시 - 사업, 반기, 분기보고서)
        """
        url = f"{self.base_url}/list.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bgn_de": bgn_de,
            "pblntf_ty": pblntf_ty, 
            "page_count": 100
        }
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
        if data.get("status") == "000":
            return data.get("list", [])
        else:
            print(f"공시 목록 조회 오류: {data.get('message')}")
            return []

    def download_document(self, rcept_no, extract_dir="data"):
        """접수번호로 공시 원문(XML/HTML) 다운로드 및 압축 해제"""
        url = f"{self.base_url}/document.xml"
        params = {
            "crtfc_key": self.api_key,
            "rcept_no": rcept_no
        }
        res = requests.get(url, params=params, timeout=30)
        if res.status_code != 200:
            print(f"문서 다운로드 실패: {rcept_no}")
            return None
            
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                z.extractall(extract_dir)
                # 압축이 풀린 파일 목록 반환
                return [os.path.join(extract_dir, name) for name in z.namelist()]
        except zipfile.BadZipFile:
            # DART API가 ZIP 파일이 아닌 에러 메시지(XML/JSON)를 반환했을 때
            error_msg = res.text[:200].replace('\n', ' ')
            print(f"다운로드 불가능한 공시입니다 (ZIP 형식 아님). 사유: {error_msg}")
            return None

    def extract_text_from_xml(self, xml_path):
        """DART XML 파일에서 텍스트와 표를 간이 추출하는 메서드"""
        from bs4 import BeautifulSoup
        
        with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f, 'xml') # DART 문서는 XML 기반
            
        # 텍스트 추출 (모든 텍스트 요소 추출)
        texts = soup.find_all(['P', 'SPAN', 'TD'])
        result = []
        for t in texts:
            text = t.get_text(strip=True)
            if text:
                result.append(text)
                
        # 간이 파싱본 반환 (실제로는 정교한 파싱 로직 필요)
        return "\n".join(result)

if __name__ == "__main__":
    collector = DartCollector()
    target_corp = "비에이치아이"
    code = collector.get_corp_code(target_corp)
    print(f"{target_corp}의 고유번호: {code}")
    
    if code:
        # 최근 1년치 공시 목록 (대략 20230101~)
        reports = collector.get_recent_reports(code, "20230101")
        print(f"조회된 공시 수: {len(reports)}")
        for r in reports:
            print(f"- {r['report_nm']} (접수번호: {r['rcept_no']})")
            
        if reports:
            # 첫 번째 보고서 하나 다운로드 테스트
            first_report = reports[0]
            print(f"\n[{first_report['report_nm']}] 원문 다운로드 테스트...")
            files = collector.download_document(first_report['rcept_no'])
            print(f"다운로드된 파일들: {files}")
            
            if files:
                # 추출 테스트
                sample_text = collector.extract_text_from_xml(files[0])
                print(f"추출된 텍스트 첫 500자: \n{sample_text[:500]}")
