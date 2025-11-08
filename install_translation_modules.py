import subprocess
import sys

def install_translation_modules():
    print("번역 모듈 설치 중...")
    print("=" * 50)
    
    modules = [
        ("googletrans==4.0.0rc1", "Google 번역 (권장)"),
        ("transformers", "Hugging Face 번역 (선택)"),
        ("torch", "PyTorch (Hugging Face 사용 시 필요)")
    ]
    
    for module, description in modules:
        print(f"\n{description} 설치 중: {module}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
            print(f"✓ {module} 설치 완료")
        except subprocess.CalledProcessError as e:
            print(f"✗ {module} 설치 실패: {e}")
    
    print("\n" + "=" * 50)
    print("설치 완료! 서버를 재시작하세요.")

if __name__ == "__main__":
    install_translation_modules()

