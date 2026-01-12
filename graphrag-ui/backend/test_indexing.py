#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到 sys.path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 導入並測試
from main import run_real_indexing, indexing_state

async def test():
    print('開始測試 run_real_indexing...')
    print(f'初始狀態: {indexing_state}')
    
    try:
        await run_real_indexing()
        print(f'完成後狀態: {indexing_state}')
    except Exception as e:
        print(f'錯誤: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
