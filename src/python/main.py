
import argparse
from stv_election import SingleTransferableVote

def main():
    """コマンドライン引数を解析し、選挙プロセスを開始する"""
    parser = argparse.ArgumentParser(description="ミーク法（ドループ基数固定版）によるSTV選挙シミュレーション")
    
    parser.add_argument("--filepath", type=str, required=True, help="投票データが記載されたファイルへのパス")
    parser.add_argument("--candidates", type=str, required=True, help="候補者記号の文字列 (例: 'ABCDE')")
    parser.add_argument("--num_winners", type=int, required=True, help="当選者数")
    parser.add_argument("--verbose", action="store_true", help="詳細な途中経過を出力する")
    
    args = parser.parse_args()
    
    candidate_names = list(args.candidates)
    
    election = SingleTransferableVote(
        candidate_names=candidate_names,
        num_winners=args.num_winners,
        verbose=args.verbose
    )
    
    election.run_election(args.filepath)

if __name__ == "__main__":
    main()
