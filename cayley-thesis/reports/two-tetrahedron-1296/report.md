# 固定兩四面體 1296 案

{"assignments": 1296, "accepted": 66, "prefixes": 216, "prefix_status": {"INELIGIBLE": 198, "SUPPORTED": 18}, "state_groups": 9, "shared_groups": 9, "distinct_history_same_completion_comparisons": 54, "both_accepted": 27, "counterexamples": 0}

固定前三次貼合為歷史，第四次為共同後續貼合。排列索引0..5依lexicographic順序。

## 共享增強狀態案例

[(0, 0, 0), (2, 2, 0)]
{'left': '0000', 'right': '2200', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '0003', 'right': '2203', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '0004', 'right': '2204', 'both_accepted': True, 'same_homology': True, 'counterexample': False}

[(0, 0, 3), (2, 2, 4)]
{'left': '0030', 'right': '2240', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '0033', 'right': '2243', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '0034', 'right': '2244', 'both_accepted': True, 'same_homology': True, 'counterexample': False}

[(0, 0, 4), (2, 2, 3)]
{'left': '0040', 'right': '2230', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '0043', 'right': '2233', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '0044', 'right': '2234', 'both_accepted': True, 'same_homology': True, 'counterexample': False}

[(1, 5, 0), (4, 3, 0)]
{'left': '1500', 'right': '4300', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '1503', 'right': '4303', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '1504', 'right': '4304', 'both_accepted': True, 'same_homology': True, 'counterexample': False}

[(1, 5, 3), (4, 3, 4)]
{'left': '1530', 'right': '4340', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '1533', 'right': '4343', 'both_accepted': True, 'same_homology': True, 'counterexample': False}
{'left': '1534', 'right': '4344', 'both_accepted': True, 'same_homology': True, 'counterexample': False}

本輪是完整歷史核對；同調映射的相等比較僅支援內部H1為0或Z。未支援者沒有當成不相等或成功。原始逐案links、拒絕原因及通過者整數證書見cases。