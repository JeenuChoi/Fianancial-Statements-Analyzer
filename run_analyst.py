import os
import glob
from dart_collector import DartCollector

def load_rag_documents(rag_dir="analyst_brain"):
    """analyst_brain 폴더에 있는 모든 마크다운 지식 문서를 로드합니다."""
    rag_docs = {}
    for filepath in glob.glob(os.path.join(rag_dir, "*.md")):
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            rag_docs[filename] = f.read()
    return rag_docs

def generate_analyst_prompt(corp_name, dart_text, rag_docs):
    """
    RAG 지식과 파싱된 DART 공시 텍스트를 결합하여 
    LLM(또는 에이전트)에게 전달할 최종 프롬프트를 생성합니다.
    """
    
    # 1. 마스터 프롬프트 로드
    with open("prompt.md", 'r', encoding='utf-8') as f:
        master_prompt = f.read()
        
    # 2. RAG 지식 결합 (Analyst Brain)
    rag_context = "\n".join([f"=== [{k}] ===\n{v}" for k, v in rag_docs.items()])
    
    # 3. 최종 프롬프트 조립
    final_prompt = f"""
{master_prompt}

--------------------------------------------------
[20년차 애널리스트의 노하우 지식베이스 (RAG Context)]
다음의 지침들을 적극 활용하여 데이터를 분석하라:
{rag_context}
--------------------------------------------------

[분석 대상 기업: {corp_name}]
아래는 수집된 최근 공시 자료의 간이 파싱 텍스트이다. 
이를 바탕으로 상단의 마스터 프롬프트 출력 포맷에 맞춰 리포트를 작성하라.

[공시 원문 텍스트 (요약본)]
{dart_text[:15000]} # 토큰 제한을 위해 1.5만자로 제한 (실제로는 정교한 청킹 필요)
"""
    return final_prompt

if __name__ == "__main__":
    corp_name = "비에이치아이"
    
    # 1. RAG 지식 로드
    rag_docs = load_rag_documents()
    print(f"RAG 지식 문서 {len(rag_docs)}개 로드 완료.")
    
    # 2. 공시 수집 및 파싱 (DartCollector)
    collector = DartCollector()
    code = collector.get_corp_code(corp_name)
    
    if code:
        reports = collector.get_recent_reports(code, "20240101", pblntf_ty='A')
        if reports:
            target_report = reports[0]
            print(f"[{target_report['report_nm']}] 파싱 중...")
            files = collector.download_document(target_report['rcept_no'])
            if files:
                # 첫 번째 XML 파일에서 텍스트 추출
                parsed_text = collector.extract_text_from_xml(files[0])
                print(f"공시 텍스트 추출 완료: 총 {len(parsed_text)}자")
                
                # 3. 에이전트용 프롬프트 생성
                final_prompt = generate_analyst_prompt(corp_name, parsed_text, rag_docs)
                
                # 테스트용으로 파일에 저장
                output_file = f"{corp_name}_agent_prompt.txt"
                with open(output_file, "w", encoding='utf-8') as f:
                    f.write(final_prompt)
                
                print(f"\n최종 에이전트 프롬프트가 '{output_file}'에 저장되었습니다.")
                print("이 텍스트를 LLM(Claude/GPT)에 복사하여 붙여넣으면 완벽한 분석 리포트가 생성됩니다.")
        else:
            print("최근 정기공시가 없습니다.")
