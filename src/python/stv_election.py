
from __future__ import annotations
import math
from typing import List, Dict, Optional

class Candidate:
    """候補者一人の状態を管理するクラス"""
    def __init__(self, name: str):
        self.name: str = name
        self.votes: float = 0.0
        self.is_winner: bool = False
        self.is_loser: bool = False
        self.keep_rate: float = 1.0

    def __repr__(self) -> str:
        return f"Candidate({self.name}, votes={self.votes:.4f}, keep_rate={self.keep_rate:.4f})"

class Vote:
    """投票用紙一枚の状態を管理するクラス"""
    def __init__(self, preferences: List[str]):
        self.preferences: List[str] = preferences

class SingleTransferableVote:
    """ミーク法（ドループ基数固定版）による選挙プロセスを管理するクラス"""
    
    MAX_ITERATIONS = 1000
    CONVERGENCE_THRESHOLD = 1e-9

    def __init__(self, candidate_names: List[str], num_winners: int, verbose: bool = False):
        self.candidates: Dict[str, Candidate] = {name: Candidate(name) for name in candidate_names}
        self.votes: List[Vote] = []
        self.num_winners: int = num_winners
        self.droop_quota: int = 0
        self.verbose: bool = verbose

    def run_election(self, filepath: str):
        print("選挙プロセスを開始します...")
        self._load_data(filepath)
        if not self.votes:
            print("有効な投票がありませんでした。選挙を終了します。")
            return
        self._calculate_droop_quota()
        self._run_main_loop()
        self._display_final_results()

    def _load_data(self, filepath: str):
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    prefs = list(line)
                    unique_prefs = list(dict.fromkeys(prefs))
                    if len(prefs) != len(unique_prefs) or not all(p in self.candidates for p in prefs):
                        if self.verbose: print(f"無効票: {line}")
                        continue
                    self.votes.append(Vote(prefs))
            print(f"{len(self.votes)}件の有効票を読み込みました。")
        except FileNotFoundError:
            print(f"エラー: ファイルが見つかりません: {filepath}")
            self.votes = []

    def _calculate_droop_quota(self):
        self.droop_quota = math.floor(len(self.votes) / (self.num_winners + 1)) + 1
        print(f"当選基数（ドループ基数）: {self.droop_quota}")

    def _run_main_loop(self):
        round_num = 1
        while True:
            active_candidates = [c for c in self.candidates.values() if not c.is_winner and not c.is_loser]
            
            if len(active_candidates) <= self.num_winners:
                print(f"\n--- 最終ラウンド: {round_num} ---")
                self._run_meek_iteration() # Run final calculation
                print("\n選挙の勝者が確定しました。")
                for c in sorted(active_candidates, key=lambda x: x.votes, reverse=True):
                    # As per rulebook, winners must EXCEED quota.
                    if c.votes > self.droop_quota:
                        c.is_winner = True
                    else:
                        c.is_loser = True
                break

            print(f"\n---ラウンド {round_num} ---")
            self._run_single_round()
            round_num += 1

    def _run_single_round(self):
        self._run_meek_iteration()
        # In regular rounds, we only eliminate, not elect.
        self._eliminate_loser()

    def _run_meek_iteration(self):
        """ロジックに基づき、保有率が収束するまで反復計算を行う"""
        for c in self.candidates.values():
            if not c.is_winner and not c.is_loser:
                c.keep_rate = 1.0

        if self.verbose: self._display_round_summary("反復計算 開始時")

        for i in range(self.MAX_ITERATIONS):
            previous_keep_rates = {c.name: c.keep_rate for c in self.candidates.values()}
            self._recalculate_votes()

            for c in self.candidates.values():
                if not c.is_winner and not c.is_loser and c.votes > self.droop_quota:
                    c.keep_rate *= (self.droop_quota / c.votes)

            rate_changed = sum(abs(c.keep_rate - previous_keep_rates.get(c.name, 0)) for c in self.candidates.values())
            if self.verbose: print(f"  [反復 {i+1}] 保有率変動: {rate_changed:.6f}")
            if rate_changed < self.CONVERGENCE_THRESHOLD:
                if self.verbose: print("  保有率が収束しました。")
                break
        else:
             print("警告: 最大反復回数に達しても保有率が収束しませんでした。")
        
        self._recalculate_votes()
        if self.verbose: self._display_round_summary("反復計算 終了時")

    def _recalculate_votes(self):
        """現在の保有率に基づき、全候補者の票をゼロから再計算する"""
        for c in self.candidates.values(): c.votes = 0
        for vote in self.votes:
            vote_value = 1.0
            for pref_name in vote.preferences:
                if vote_value < self.CONVERGENCE_THRESHOLD: break
                candidate = self.candidates[pref_name]
                
                current_keep_rate = 0.0
                if not candidate.is_winner and not candidate.is_loser:
                    current_keep_rate = candidate.keep_rate
                
                transfer_value = vote_value * current_keep_rate
                candidate.votes += transfer_value
                vote_value -= transfer_value

    def _elect_winners(self) -> bool:
        elected_this_round = False
        for c in sorted([c for c in self.candidates.values() if not c.is_winner and not c.is_loser], key=lambda x: x.votes, reverse=True):
            if c.votes > self.droop_quota:
                c.is_winner = True
                elected_this_round = True
                print(f"当選: {c.name} (得票数: {c.votes:.4f})")
        return elected_this_round

    def _eliminate_loser(self):
        active_candidates = [c for c in self.candidates.values() if not c.is_winner and not c.is_loser]
        if not active_candidates: return

        min_votes = min(c.votes for c in active_candidates)
        
        for c in active_candidates:
            if abs(c.votes - min_votes) < self.CONVERGENCE_THRESHOLD:
                c.is_loser = True
                print(f"落選: {c.name} (得票数: {c.votes:.4f}) - 最下位")

    def _display_round_summary(self, timing: str):
        print(f"  --- {timing} --- ")
        for c in sorted(self.candidates.values(), key=lambda x: x.name):
            status = "当選" if c.is_winner else "落選" if c.is_loser else "活動中"
            print(f"    {c.name}: {c.votes:.4f} ({status}) [保有率: {c.keep_rate:.4f}]")

    def _display_final_results(self):
        print("\n--- 選挙結果 ---")
        winners = sorted([c for c in self.candidates.values() if c.is_winner], key=lambda x: x.name)
        
        print(f"当選者 ({len(winners)}名):")
        for c in winners:
            print(f"  - {c.name}")

        print("\n最終状況:")
        for c in sorted(self.candidates.values(), key=lambda x: x.name):
            status = "当選" if c.is_winner else "落選"
            print(f"  - {c.name}: {c.votes:.4f} ({status}) ")
