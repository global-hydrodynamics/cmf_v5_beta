# CaMa-Flood v5 β01 開発分析ノート

- 作成日：2026-11-20（日本時間）
- 位置付け：研究室内向けの事後的な開発分析。公開用リリースノート・性能評価・科学的検証報告ではない。
- 作成方法：Codexによる資料照合と分析。研究者による内容確認を要する。
- 分析対象のソース到達点：`507f136fc39d7a525947f6c3f02a7a4a79d26b13`（2026-11-19、`package v5b01`）。調査時の作業ブランチは `feature/package-builder`。
- 統合状況：`origin/main` の `d433b596fe912b3ba62ebd6830f1eb0a3f3e3d6d` は上記を取り込んだPR #4のマージであり、両者のファイル内容に差分はない。
- 区切りの扱い：調査時にローカルタグはなく、GitHub Releases APIにもReleaseはなかった。したがって上記を**β01分析の暫定ソース境界**とし、正式なタグ付きリリースや最終パッケージの検証完了とは解釈しない。

## 要旨

β01で進んだのは、新しい水理モデルへの置換ではなく、既存のCaMa-Floodを「仕様と根拠を追いながら扱える開発対象」にするための整備である。モデル本体、前処理、Runoff、教材、可視化、配布を別々に改善しつつ、その間の単位・配列・ファイル・実行経路の契約を明示した。中心的な成果は、`src_main/` のv5開発系、Binary/NetCDFの個別Map入力と出力・Restart整理、共有前処理、CSVによる変数定義、Mekong実行例、仕様に基づく教材作成、GalleryとMap Explorer、ソースと追加データを分離するパッケージ作成である。

これらの実装には、限定した条件での旧実装との一致、Mekongの実行、形式変換の原値比較、GUI・PNG確認などの記録がある。ただし、ある時点の小地域・特定ビルドでの一致を、全構成・最新ソース・配布物・科学的妥当性へ広げることはできない。β01の到達点は、作業経路と検証境界を可視化した内部ベータであり、承認済みの包括的な科学回帰基盤が完成した状態ではない。

協働では、研究者が科学的意味と受け入れ条件を決め、ChatGPTが論点・仕様を整理し、Codexがソース調査・実装・検証・記録を進める役割分担が文書化された。一方、実際の改善は一方向の引き渡しでは完結していない。UIの使いにくさ、意味の取り違え、過剰な一般化、実データで初めて表面化する制約を研究者が指摘し、仕様と実装を反復修正した。AIの自律性を高めるには、判断権限だけでなく、変更してはいけない科学的契約と、停止せず進められる範囲を具体化する必要があった。

本ノートでは2026-10-25から11-19までを20のエピソードに再構成する。コミット数、変更行数、タスク数を生産性や科学的品質の指標には用いない。β02では、最新ソースと配布物の再現可能な受け入れ確認、代表的回帰条件の研究者承認、既存仕様の発見・再利用を優先する。Skills化は候補の提案までとし、実装しない。

## 調査の範囲と読み方

### 資料と証拠の階層

本ノートは[研究記録の規約](README.md)と[研究計画](study_protocol.md)に合わせ、知識へのアクセス可能性、再現性、拡張性、ガバナンスの四側面を軸とする。主に次の資料を照合した。

| 資料 | 用途 | 解釈上の限界 |
| --- | --- | --- |
| [AGENTS.md](../AGENTS.md)、設計・開発規約 | 権限、保存条件、目標、設計上の意図 | 現在の規則が過去の全作業に適用済みとは限らない |
| ソース、README、CSV、代表コミットの差分 | 実装された経路と到達点 | コードだけから歴史的動機・科学的根拠を断定しない |
| [events.csv](events.csv)、[development_tasks.csv](development_tasks.csv) | 指示・判断・実装・検証の関係 | 逐語的な対話記録でも全作業の観測でもない |
| DR、HI、KG、ADR | 研究者の説明、介入、不明点、判断 | AI作成の要約には研究者確認が必要 |
| [validation_runs.csv](validation_runs.csv)とVR詳細 | 実施条件、比較方法、結果、未実施事項 | 過去のPASSは最新HEADの再試験結果ではない |
| Stage要約、Git履歴、main統合 | 長期的な構成と時系列の照合 | 同期・整理コミットを独立した成果とは数えない |

以下の「確認」は読んだソース・差分・明示的な記録に支えられる事項、「分析」はそれらを横断した本ノートの解釈、「未確認」は資料不足を意味する。既存VRに書かれた実行結果は**当時の記録として確認**したもので、今回再実行した結果ではない。本調査ではモデル計算、図生成、パッケージ再作成、ブラウザ操作を行っていない。

### 開始点とGitの解釈

文書整備の開始は `680bf133ac487f760fed99f547e6a960706d9342`（2026-10-25、`AGENTS.md` と `docs/dev_status.md` の追加）である。その直前の基準は `1c7b667d8f23d31a0fb913d7650f969016d704a5`。この基準にも文書やテストは存在しており、「文書のない原型」や正式なv4.30リリースではない。[基準点の調査](baseline/pre_documentation.md)には歴史的な `research-baseline-pre-document` というタグ名の記載があるが、今回のローカルタグ一覧に存在するとは限らない。

初期の文書整理は `docs/reorganization` とPR #121、v5モデル開発は `feature/gosh-refactor`、後期の配布作業は `feature/package-builder` に関係する。ただしブランチは分析上の章区分ではない。旧リポジトリの証拠URLも、その履歴を示す参照として保持する。

Gitは実装の履歴であると同時に、複数の作業機間の同期手段でもあった。コミットの時刻は保存・同期の時刻であり、議論や実装開始の時刻とは限らない。たとえば最後の `507f136f` は、CTL、COG、パッケージ名称、ベータの位置付けをまとめて含む。逆に一つのI/O改善が実装・検証参照・文書整理の複数コミットに分かれる。以下の期間は関連イベント・差分が存在する日付の範囲であり、労働時間ではない。

E01–E20は本ノート内の編集上の単位であり、新たな研究Task IDではない。既存のDT/VR等へ参照を付ける。依頼範囲に合わせ、既存の研究インデックスや過去の記録は書き換えない。

# 第I部　技術的成果と到達点

## 1. モデル本体：開発系の分離とI/Oの見通し

### 1.1 v5開発系を独立させる

`src_main/` と、後に `gosh_test/` へ整理される実行例は、旧 `src/`・`gosh/` 系を保護しながらv5を進めるために作られた。最初は機能ディレクトリを含むソース全体をコピーし、v5側だけをビルドする経路を確立した。これはICI、sediment、heatlink等をすべてv5で検証・サポートしたことを意味しない。[モデル開発Stage記録](stages/model-source-workflow.md)、DT-0041、VR-0082が初期境界を示す。

現在の標準実行ファイルは `src_main/MAIN_cmf`。機械依存のv5ビルド設定は `config/Mkinclude` に分け、旧v4の `adm/Mkinclude` へ暗黙に戻らない。環境診断と設定の有効化も分ける。これは利用者が「どのソース・設定でコンパイルしたか」を見失わないための整備である。

### 1.2 読みやすさと科学的保存条件

[FORTRAN_DESIGN.md](../src_main/FORTRAN_DESIGN.md)は、主要な `CMF_*` 処理と `_UTIL_` 補助処理、責任を持つモジュール、I/O契約、精度、並列性、ログを整理する。[FORTRAN_STYLE.md](../src_main/FORTRAN_STYLE.md)はその局所的な表現を扱う。両者を分けることで、整形のたびに全体設計をやり直したり、命名だけから意味を推測したりすることを避ける。

特に、`D2` 等の歴史的名称は現在の配列rankを保証しない。浮動小数点の式・加算順序、kind、閾値、Mapからvectorへの変換、Restart時機、OpenMP/MPIの意味は、可読性改善だけを理由に変更しない。β01の成果は、これらを全ソースで完全に統一したことではなく、新規・重点改修箇所で守る判断基準を明文化したことである。

### 1.3 Map入力・Forcing・Output・Restart

個別Map入力は既存のBinary経路を対象に `.bin` / `.nc` を選べるようにし、混在も扱う。既存の `LMAPCDF` による統合NetCDF入力とは別経路である。初期実装で対象を広く解釈したslope系は個別入力から外し、旧統合形式側の制約を明示した。その後、旧NetCDFハンドルの寿命に関する不具合は別タスクで修正した。対象拡張と不具合修正を分離した点が重要である。証拠はDT-0047–0049、[ADR-0005](records/decisions/ADR-0005-map-input-path-scope.md)、[ADR-0006](records/decisions/ADR-0006-legacy-netcdf-handle-lifecycle.md)。

ForcingではDAY/MON/YEAR/SEQのファイル群とレコード選択を整理し、重複した `LINPDAY` インターフェースを除いて日付規則を明確化した。OutputではCSVの変数定義・alias、キャッシュした定義の参照、明示的なデータ振り分け、型別generic writerを組み合わせた。これは任意の配列が自動的に出力できる万能APIではなく、どのモデル量を出力するかはソースで明示する設計である。Restartでは保存対象状態の選択とBinary/NetCDF表現を分け、主要処理から保存状態の一覧を読めるようにした。

直接の実装参照は [Map入力](../src_main/cmf_ctrl_maps_mod.F90)、[Forcing](../src_main/cmf_ctrl_forcing_mod.F90)、[Output](../src_main/cmf_ctrl_output_mod.F90)、[Restart](../src_main/cmf_ctrl_restart_mod.F90)である。検証の強さは段階で異なる。初期の40日間I/O比較には、同一環境で選択した出力のbyte一致がある。一方、Output再構成のVR-0112では改修前の出力基準がなく、現ビルド内のalias一致等が中心である。後者を「旧実装との完全一致」と読み替えてはならない。RestartのVR-0117はNormalの前後比較、Storage-onlyの実行等を含むが、全optional構成を覆わない。[VR-0091](records/validation_runs/VR-0091.md)、[VR-0112](records/validation_runs/VR-0112.md)、[VR-0117](records/validation_runs/VR-0117.md)。

### 1.4 科学的・数値的変更を構造変更と混同しない

大半の作業は既存計算の保存を目的とするが、履歴全体を「数値変更なし」と総括することも不正確である。`6adceff0` は実験的な `CMF_OPT_FLDSTG_SIMD` を大きく変更し、研究者はrefactor中に見つかったbugへの対処と説明している。ただし具体的な不具合の再現条件は記録されていない。当時の調査では通常のdispatcherからこのSIMD処理は呼ばれず、標準計算への影響や高速化を実証したものではなかった。独立した未完の検証対象として扱う。[DR-0059](records/discussions/DR-0059.md)。

もう一つ、Runoff climatologyの沿岸補正maskは承認された動作変更である。1981–2010の実データ比較では64,800セルのうち旧referenceとの完全一致は49,789セル（約76.83%）、旧referenceで0だった807セルが正値になった。同じmaskを使うsynthetic比較での旧新一致と、この実データの差は両立する。新しい全体を旧referenceと科学的に交換可能と宣言する根拠はなく、KG-0037を残した。[VR-0164](records/validation_runs/VR-0164.md)はこの境界を明記している。

## 2. Map前処理と変数定義

### 2.1 共通コードとMap固有設定

`map/tools/code/` に処理を集め、`script_region/`、`script_params/`、`script_analysis/`、`script_format_conv/` とMapローカル例を用意した。単なるファイル移動ではなく、共有実行コードとユーザーが読む設定・手順を分けた構成である。旧 `map/src/` の履歴や現存依存は残り、v4領域を全面的に廃止したわけではない。

地域抽出、分岐・流域処理、MPI区分、永久水面、観測点・ダム・水位点のallocation、上流域・小流域分析を段階的に移行した。MPI前処理の旧新一致は、分割後のモデル実行や分岐経路の省略が科学結果に与える誤差の検証とは別である。Allocationも選択した事例での互換性と単一高解像度領域という契約を持ち、多領域の一般的な正確さを保証しない。[Map-tools Stage記録](stages/map-data-tools.md)。

Shellは手で実行するコマンド列を読みやすく示し、科学処理と詳細検証はFortran/Python側に置く方針になった。これは安全性を捨てる意味ではなく、失敗時停止・安全な後始末・明示的に必要な対話は保ちながら、過剰なwrapper化で処理順序を隠さない判断である。

### 2.2 CSVは表記集から契約の共有点へ

現在の定義は [variable_table/](../variable_table/README.md) に整理され、Map、Output、Restartの表を持つ。Map表には型、配列・record、単位、欠損値、特殊値、用途、由来等を区別して記す。`workflow_stage` は研究者管理であり、ファイルの存在だけでAIが `default` と判定してはいけない。

意味の回復は重要な成果である。`lonlat.bin` は単純なGrid中心ではなくOutlet座標を持つ。粗いMapの `uparea` はm²、高解像度 `uparea` はkm²であり、同名でも単位を流用できない。`catmxy` は1-basedの粗い河川セルへの割当で、`nextxy` は河川セル間の接続である。`catmz100` 等のprofileは処理段階で非集水域コードが変わることがある。これらはファイル名や見た目から推測せず、producer・consumer・研究者説明を照合して整理した。

ただしCSVを唯一の真理とみなせばよいわけではない。未確認値は未確認として残し、ソース・データとの矛盾を記録する必要がある。`prmwat` の5 m基準では、説明上の `<` と実装の `<=`、数値自体の由来を分けて保留した。移行時にAIの解釈で閾値を変えなかった点は科学的保存の具体例である。[ADR-0004](decisions/ADR-0004-prmwat-semantics-and-legacy-contract.md)、[VR-0058](records/validation_runs/VR-0058.md)。

## 3. Runoff、実行例、教材

### 3.1 入力データを計算条件として説明する

Runoff整備は[データinventory](../docs/runoff_data_inventory.md)、`inp/` の手順、取得・変換コード、sampleの由来を接続した。時刻の意味、積算と平均、`DROFUNIT`、Grid・期間・recordの対応を個別に確認する必要があった。元データ取得とモデル入力形式への変換は別の責任であり、外部サービスへの接続成功やデータ再配布まで自動的に保証されない。

Mekongの小規模入力とInput Matrixを利用して実行可能性を確かめ、年間NetCDFやJapanの集約sampleなどを整えた。粗いRunoff Grid上のclimatologyと沿岸最小値処理も、単に水路パラメータへ名前を合わせるのではなく、入力側Gridとモデル側の意味の違いを明示する対象となった（DT-0118／VR-0164）。現在のデータ名と歴史的な `test-*` 名は区別して読む。

### 3.2 実行例の差は必ずしも不整合ではない

`gosh_test/mek01-default_run.sh` は `nextxy_noedge.bin`、`mek02-2year_netcdf.sh` は `nextxy.nc` を意図的に使う。これはExplorerで全 `nextxy` を描く方針とは用途が違う。名前を一律にそろえる改修は不適切である。Input Matrixの `test-mek_1deg` も、Runoffデータセットの `repo-mek_1deg` 等とは独立した既存Grid契約であり、名前の違いだけで再生成する必要はない。

実行場所に依存しないルート取得、`CVARSOUT` に対応する再実行時削除、年次Restartとログの扱いは、科学設定を変えずに実験を再実行しやすくする改善である。削除確認は一時ディレクトリで実施したと記録される（DT-0131／[VR-0177](records/validation_runs/VR-0177.md)）。

### 3.3 教材を仕様・実装・説明に分ける

[tutorial開発方針](../docs/tutorial_development_plan.md)と[作成ガイド](../tutorial/how_to_develop_tutorials.md)は、まず実験仕様をソース・データと照合し、その後に実装・実行・図・説明を作る順序を定めた。Tutorial01では実行経路、出力隔離、初心者への情報提示、resetを反復改善した。Tutorial02では当初の三実験案を、そのまま実装せず、Kinematic Waveと分岐・時間刻みの制約を調査して研究者の四実験設計へ改めた。

四実験はDefault、No Bifurcation、Kinematic Wave、No Floodplain。2000–2003の16年区間の完走記録はあるが、逆流の解釈、spin-up十分性、観測との一致を確定したものではない。Tutorial02の実装・図と、今後作る学習者向けマニュアルは分ける。後期にはTutorial01でコンパイル済みの `src_main/MAIN_cmf` をTutorial02とGuide01で再利用し、教材間で実行ファイル経路を統一した。[VR-0123](records/validation_runs/VR-0123.md)、[VR-0125](records/validation_runs/VR-0125.md)、DT-0145–0147。

## 4. 可視化：科学表現の再利用と操作性

### 4.1 Galleryの意味を共有する

[visualization_catalog.csv](../visualization/visualization_catalog.csv)はFigure、method、option、必要変数、説明・実装への参照をつなぐ。Grid中心の線、実Outlet間のvector、分岐、Unit Catchment、channel pixel、高解像度地形を意味で区別した。描画できたことと、Galleryとして承認・公開できることも分けた。

たとえばp01-f04aはChannel分岐、f04bはChannel＋Overland分岐を比較できる構成へ修正された。`nextxy_noedge` による描画省略を除き、Blue-to-Navy等のGallery定義とExplorerを合わせた。一方、この可視化方針をGOSHの計算条件に持ち込んではいけない。[River Map README](../visualization/river_map/README.md)、DT-0124／VR-0170。

### 4.2 Explorerは科学データの別表現である

[Map Explorer](../visualization/map_explorer/README.md)は、計算を起動せずMapを読む独立したGUIとして始まり、左のMapを維持した右側設定、Visualization/Inspector切替、Gallery preset、クリック選択、Pins、PNG/CSV/JSONへ発展した。現在のPython実装はアプリ直下ではなく `code/` にある。

共有presetは軽量な `presets.csv` がcanonical catalogを参照し、科学説明の別registryを作らない。ユーザー状態のJSONとは役割を分ける。新規起動とMap切替では、必要データがあればp01-f04bを適用する。Mapを切り替えてもすべてにMekongの範囲を押し付けず、製品が足りない場合は不足理由と利用可能な表示を示す。

選択ではクリック位置、native pixel、assigned river cell、Outlet、downstream linkを区別する。Unit Catchmentの輪郭はnative `catmxy` の同一pairに属するpixelの露出辺から作り、粗いGrid矩形や `nextxy` の上流追跡で置換しない。穴や離れた成分を勝手につながない。Inspectorの粗い `uparea` と真の高解像度 `uparea`、Pixel数と物理面積も別物である。選択Gridの淡紫破線、選択Catchmentのオレンジ輪郭、Outlet接続の黄色は、別の幾何を示す。

BrowserとPNGは科学的なscene・座標・色範囲を共有するが、画面全体の複製ではない。OSMはオンラインの背景で、ローカルMatplotlibのPNGには含めず通知する。Pinsや科学レイヤーは保持する。GUIと出力の違いも仕様として説明する必要がある。

### 4.3 表示の近似を科学的選択から分離する

広域・高解像度では、元のNetCDFだけを都度大きく読む構成に限界が現れた。COGはモデル入力の置換ではなく表示用cacheとして導入し、Overviewとnative windowを利用する。カテゴリ値・assignmentを平均画像から再推定しないこと、原値と座標を保存することが条件である。[format conversion README](../map/tools/script_format_conv/README.md)、[Explorer設計](../visualization/map_explorer/DESIGN.md)。

現行Autoは通常の連続値でP5/P95。高解像度は有効なpaired `catmxy` と粗いGrid範囲を検証し、海・未割当・不正割当・欠損を除く。粗い `uparea` を継承する背景は有効pixelごとに値を与えるpixel頻度重みであり、各粗いセル一票でも物理面積重みでもない。Logのpercentileには有限の非正値も含め、P5が正ならその値を保ち、P5が0以下なら0.01にする。正の値を一律0.01以上に切り上げる古い方針とは異なる。上限が下限以下なら範囲エラーとし、Manualは勝手に書き換えない。

50 million native pixelsを超えるtileでは、研究者承認の後、固定した12×12の層ごとの最大16×16 patch、最大36,864 pixelから**近似P5/P95**を得る。viewportや描画Overviewから統計を作る方法ではなく、原データからの限定sampleである。ただし稀な地物を見落とし得て、厳密percentileとの同等性や不偏性は主張しない。複数tileの合成も全tile統計ではなく、最初の描画tileのreferenceに依存する。表示の近似を明記した上で、選択値・native境界は別経路で扱う。[VR-0182](records/validation_runs/VR-0182.md)。

また、粗いGrid線は縦または横が30セル以上なら全体を隠し、間引いた線を元の解像度のように見せない。河川は閾値を超えたときに最上流の最初のlinkだけを省略し、内部linkを保つ。端点の `-10` は地域切り出しの域外接続でも現れるため「物理的な内陸河口」と断定せず、`-9` とともに拡大時のみ表示する。Globalの選択輪郭やHeadwater guideにはvisible native windowという範囲制約がある。全Catchmentの面積・重心と誤解させないことが重要である。

## 5. 配布と再現性の基盤

[開発・配布設計](../docs/development_and_distribution_design.md)は、GitHubソース、Package Additional Data、生成された配布物の三者を分ける。追加データのimportは一方向の取り込み、diffはread-onlyの差分確認、clean archiveはcommit済みソースの抽出、package assemblyはclean sourceと選択データの組合せという異なる操作である。

現在の入口は `package/p01-archive_clean_repo.sh`、`p02-make_package.sh`、`s00-diff_package_data.sh`、`s01-install_package_data.sh`。`PACKAGE_DATA_DIR="../../cmf_v5_package_data"` の相対基準は `package/` で、呼出元CWDではない。絶対パスとdry-runも同じ規則に従う。[package README](../package/README.md)。

過去の実assemblyにはコピー内容・manifest・入力不変の確認がある。しかしclean treeが編集されていれば、そのbuild-infoにあるcommitだけで全内容のGit同一性は保証できないという事例も記録された。さらに現行の最終改修と同じソースを用いたパッケージ再作成・fresh-cloneからの通し確認を今回行ったわけではない。追加データの版管理、承認済み回帰reference、optional構成、外部開発者の共通検証環境は引き続き課題である。[VR-0187](records/validation_runs/VR-0187.md)、[KG-0036](records/knowledge_gaps/KG-0036.md)。

# 第II部　開発エピソードの再構成

以下では第I部の機能一覧を繰り返さず、問題、判断、結果、残った境界を中心に記す。日付は記録上の活動範囲であり、各決定の正確な時刻が残らない場合は断定しない。

## E01　文書と開発規則を入口にする（10月25日）

既存ソースを外部から理解しにくいという問題に対し、rootとcomponentの案内、AGENTS、開発status、compiler例を整えた。基礎コミット `680bf133` から文書PR #121の `11d3fcdf` までを一つのepisodeとする。複数コミットの時間差は作業時間ではない。Fortranの変更はなく、PR上の検証記録も十分には残らない。成果は知識の入口とルールの明文化で、理解度向上の実測ではない。[文書Stage](stages/documentation-modernization.md)、DT-0001・0003。

## E02　地域抽出をv4と並行して移す（10月30日）

v4を保護してv5の地域抽出を進めるため、五つの既存Fortran programを共有 `map/tools/code/` に移した。build場所をMap側から共有codeへ整理する過程も一連の設計調整である。`ad7d544e`、`c2b1aac`、`ea14d6b` は実装・整理の証拠となるが、compileと実Map生成は分ける。研究者のMekong生成報告は [HI-0002](records/human_interventions/HI-0002.md) にあり、当時の正確なbuild・command一式は残らない。生成成功を科学的検証としない。DT-0002、VR-0005–0008、[Stage補足](stages/map-data-tools.md)。

## E03　高解像度データの意味を回復する（10月30–31日）

CSV登録とCTL生成を進めると、Outlet、profile rank、海・未割当コード、D8方向、面積単位などの曖昧さが表面化した。公開側consumerだけでなく、許可されたFLOW producerと研究者説明を突き合わせた。raw値とmerge後の値を区別したことが重要である。成果は「未知を埋めた表」ではなく、確認済み・暫定・未解決を区別する契約である。VR-0011・0014–0019、DT-0005、[metadata仕様](../variable_table/map_metadata_spec.md)。

## E04　分岐・流域・MPI前処理を段階移行する（10月31日–11月1日）

共有化と互換性維持を両立させるため、標準分岐、流域診断、MPI aggregation、partition、表示色を別責任に整理した。途中で `mpireg.bin` aliasをやめ、番号付き成果物と任意の表示色生成を区別した。旧実装との比較は選択Mekong・synthetic・4/8/16区分等の証拠であり、分散モデル本体の検証ではない。DT-0004・0007–0017、VR-0049–0054、[前処理Stage](stages/map-data-tools.md)。

## E05　永久水面の互換性とWhyを分ける（11月1日）

`prmwat` を移す際、面積集計の旧新一致だけでは用途や5 m基準の意味を説明できなかった。研究者は、モデルが再現する浸水域から外れた孤立湖等を除く意図を説明した。しかし5 mの導出、厳密境界、欠損値の扱いには不明点が残る。byte一致を保ちつつ不明点をKGとして残した判断は、AIが「もっともらしい科学」を追加しない実例である。DT-0020・0021、VR-0057・0058、KG-0009–0011、[ADR-0004](decisions/ADR-0004-prmwat-semantics-and-legacy-contract.md)。

## E06　allocationと河川解析を共有手順にする（11月1日）

Gauge・dam・level-gaugeの二段階処理、データの由来・追跡方針、共通Map I/Oを整理し、続いて上流域・小流域・node解析を移行した。共通読込をまとめても科学的な選択処理は別に残した。研究者が選んだCSVのGit管理は、元database全体の再配布許可とは同義でない。単一高解像度領域という制約も残す。DT-0022–0032、VR-0065–0070、KG-0014。

## E07　Runoffをsampleではなく入力契約として整える（11月1–3日、後続11月16日）

取得、変換、sample作成、単位・時間規則、平均Runoffを別々に調査した。データ名、時刻の位置、積算と平均、Input Matrixを一括して推測しない方針が必要だった。後続のclimatology・沿岸処理も同じ意味の問題としてここへ結び付ける。DT-0033–0040と、並行作業後にcanonical IDが変わったDT-0118は一つの入力整備の流れとして扱う。ただし元の判断日は統合日から逆算しない。[Runoff inventory](../docs/runoff_data_inventory.md)、VR-0072–0077、[VR-0164](records/validation_runs/VR-0164.md)。

## E08　v5モデルの最初の実行基盤を作る（11月3日）

コピー・compileのみの段階から、Mekong年間実行、40日例、時間・終了status、CTLへ進んだ。最初の年実行と、後に短くしたdefault例を混同しない。8,784 timestepの完走は当時の年間条件の動作証拠であり、v4との数値同一性ではない。DT-0041–0045、VR-0082–0085、[モデルStage](stages/model-source-workflow.md)。

## E09　NetCDFと混在Map入力を比較で確かめる（11月3–4日）

別buildのNetCDF I/O、年間forcing、年次Restart、個別Map入力を順に追加した。40日比較と二年実行を一つのPASSにまとめず、比較した形式と変数を限定して読む。slope経路の過剰な対象拡張を戻し、handle bugは独立に直した。これにより形式追加と科学仕様追加を切り分けられた。DT-0046–0061、VR-0087–0106、ADR-0005・0006。

## E10　Forcing・Output・Restartを再構成する（11月4–5日）

ファイル群の時間規則、Output registry・alias、分岐表CSV/NetCDFとpath identity、Restart stateと表現を整理した。Fortran genericを採用しても主要な状態選択とデータ対応は可視のまま残した。`973ddacf`、`2f9d0e90` 等の構造変更、`f7e23330` の分岐I/O、実験SIMDの `6adceff0` は同日に存在しても同じ科学的変更ではない。検証基準がない部分を明記することが重要だった。DT-0062–0073、VR-0107–0118、DR-0059。

## E11　環境準備を診断と明示操作へ分ける（11月5–8日）

Fortran/Python setupとv5のbuild設定を整理した。ローカル設定を黙って書き換えず、診断、提案、確認、ユーザーによる有効化を分けた。Mekong実行が成功してもPython依存の取得がDNSで失敗した例があり、環境構築を一つの成功判定にしない必要があった。DT-0074・0081、VR-0119・0124・0125。

## E12　実験仕様からTutorial02を作る（11月5–8日、更新11月19日）

当初案は三実験だったが、ソース上のKinematic Wave・分岐・初期化・出力時刻の制約を確認し、研究者承認の四実験へ改めた。`81ada013` は仕様改訂、`7be4b694` は実装・実行の代表点である。16区間の完走、逆流や分岐の違いの図は得たが、観測比較の精度評価ではない。後に六地点のdelta比較等を追加し、最終的には共通実行ファイルへ整合させた。学習者向けmanualの作成完了とはしない。DT-0075–0078・0090・0091・0146、VR-0123・0133・0192。

## E13　Tutorial01と作成方法を反復改善する（11月8日、更新11月19日）

初回manualの実行を入口に、共有ガイド、個別仕様、教材配置、独立script、出力隔離、情報の導入順序を調整した。一回生成した文章を完成品とせず、初心者が何を操作し、何が意図的な演習部分かを明確にした。Guide01も後に同じbuild・実行契約へ整えた。再現性の向上は設計上の成果だが、複数の独立した学習者による効果測定はない。DT-0082–0089・0092・0145・0147、VR-0125–0135・0191・0193。

## E14　研究記録そのものを修復する（11月6日、並行統合11月16日）

欠落index、CSV列ずれ、ADR重複、移動後の参照を修復した。元のVRが見つからないものは推定台帳で承認し、存在したテスト結果として再創作しなかった。さらに二拠点の並行作業で同じDT/VR/EVを別用途に採番していたため、公開済み側を保ち、もう一方をcanonical IDへ写像した。これは記録を増やすだけでは監査可能性が保てない事例である。DT-0079・0080、[記録整合性review](records_integrity_review_20261106.md)、[ADR-0013](records/decisions/ADR-0013-reconcile-parallel-research-ids.md)。

## E15　Galleryを再利用できる語彙へ育てる（11月12–17日）

Method/optionの名前、catalog、地理範囲、colorbar配置を調整し、Grid中心、Outlet vector、分岐、Catchment、terrainを段階的に追加した。最終的なf04a/f04b比較と色定義は後続の研究者指示で修正された。IDだけでなく自然言語の方法名を残すことが、名前変更後の発見を助ける。表記統一が新しい科学的方法の創出だったとはしない。DT-0093–0101・0124、VR-0136–0147・0170、[可視化ガイド](../visualization/figure_making_guideline.md)。

## E16　GUIの表示設定と科学的選択を分離する（11月16–17日）

Explorerを短期間に反復改良した。設定tabでMapが消える、選択輪郭が背景依存になる、pixelと粗いセルの情報が混ざる等の問題を、持続するMapと独立state、Inspector、native assignmentの幾何で解決した。CSV preset、色・線・Overlay、OSM、Pinsと出力も同じepisodeの段階である。ユーザーの繰り返しの指摘は単なる見た目調整ではなく、科学的対象を操作から理解できるかの検証として働いた。DT-0105–0117・0119–0123・0126、VR-0151–0172。

## E17　大域表示で近似の境界を設計し直す（11月17日）

高密度の河川・Grid、NetCDF読込、厳密統計により、regionalで成立した操作がGlobalでは重くなる問題が現れた。広すぎる間引きを最上流linkだけへ修正し、Gridはall-or-noneとした。COG native/Overviewに対応後も、厳密統計cacheの未作成でMap自体が開けない問題が残り、研究者が表示用Sparse samplingを明示承認した。`1248a115` はVR-0182の調査元となる代表点。近似を原値・assignment・geometryへ拡張しないことが判断の中心である。DT-0128–0130・0132–0138、VR-0174–0184。

## E18　形式変換の対象発見と上書き操作をそろえる（11月17–19日）

Binary/NetCDF/COGの変換手順を `script_format_conv/` に整理し、登録変数の存在確認、summary、一括または個別overwriteを整えた。非対象の分岐表・旧統合containerは正常skipとし、真の不正入力のerrorと分けた。解像度は存在する `1min`、`30sec`、`15sec` の粗い方から簡潔に選ぶ。後期のCSV集約でMPI・sample variantの発見が抜けたため、標準定義参照を再利用してCOGとCTLへ復旧した。定義の重複を増やさず、変種のidentityと全record layoutを保持した。DT-0127・0132・0133・0135・0142–0144・0150・0151、VR-0178–0181・0188–0190・0196・0197。

## E19　配布設計から安全な生成手順へ進む（11月15–19日）

設計採用時点では仕様だった三層構成を、追加データimport/diff、clean archive、assemblyへ段階的に実装した。作業treeをそのままrelease扱いせず、commit済みソース、選択データ、manifest、入力不変、競合・再実行を扱う。途中の追加データ相対基準を `package/` に固定し、最後に番号付き入口へ変更した。過去の生成成功はあるが、最終ソースの配布受け入れ完了は未確認として残す。DT-0103・0125・0140・0141、VR-0149・0171・0186・0187、[配布設計](../docs/development_and_distribution_design.md)。

## E20　配布対象の整合性を絞ってβ01へ統合する（11月15–19日）

移行後の古いパス、データ名、実行ファイル、教材・setupの説明を照合した。研究者の指示により後期auditは生成パッケージとテストを対象外とし、配布予定ソースを修正した。この範囲制限は、未確認項目をPASSへ変えるものではない。`40f29107` は四つの配布対象不整合修正、`507f136f` はその後のCTL/COG等を含む同期・集約点である。mainへのPR #4統合は確認できるが、形式的なReleaseやクリーン環境での最終検証とは分ける。DT-0104・0139・0148・0149、VR-0150・0185・0194・0195、[audit](../docs/repository_consistency_audit_20261119.md)。

# 第III部　Human–ChatGPT–Codex協働の分析

## 6. 三者の役割と実際の往復

[AI development workflow](../docs/ai_development_workflow.md)では、ChatGPTが実装前に論点・危険・代替を整理し、研究者が科学的・構造的判断を承認し、Codexへ範囲・制約・検証条件を引き渡す。完了後は実装と証拠を再reviewする。これは規定された役割であり、すべてのepisodeが実際に同じ順序を通ったという観測ではない。

確認できる記録では、研究者は背景知識の提供だけでなく、対象範囲の絞り込み、選択の意味、UIの使い勝手、近似の許容、配布物に含める範囲、公開操作の権限を繰り返し決めている。Codexはソースが示す事実を返し、実装・比較・文書化へつなぐ。ChatGPTの全対話原本は本調査の証拠に含まれず、個々の設計案の発案者や私的な思考過程までは再構成できない。

分析として、最も有効な引き渡しは長い要望一覧そのものではなく、①承認済み判断、②保存条件、③対象外、④実施可能な受け入れ条件を分けたものである。これが曖昧だと、AIは規則を過大解釈して止まるか、科学的意味まで自律的に埋めてしまう。

## 7. 知識の外在化は「不明点を残す」作業でもある

Mapのsentinel、面積単位、Outlet、`prmwat` の用途、allocationの由来は、コードを移す途中で問題として顕在化した。ソースを読んで分かる動作と、研究者しか説明できないWhyを分け、KGから調査・説明・文書へ結ぶことで、後続の変換・可視化でも再利用できる知識になった。

[Scientific Why Discovery](../docs/ai_workflows/scientific_why_discovery.md)は、疑問を列挙し、推測回答を作らない。[Why Documentation](../docs/ai_workflows/scientific_why_documentation.md)は、既存根拠を確認してから不明点を研究者へ聞き、仮説・説明・ソース整合性を区別し、承認されたコメントだけを入れる。この工程は暗黙知の回復に有効な設計だが、β01全体の知識回収率を測定した結果ではない。

残るリスクは、後から整った文章が当時の理解まで確定していたように読めることである。未解決の5 m基準や欠落VR、未検証のoptional経路を残すことは記録の欠点ではなく、誤った確実性を防ぐために必要である。

## 8. 互換性を守る検証と科学的妥当性

β01では、source copy、byte一致、typed readback、metadata・shape・日時、Restart handoff、synthetic fixture、GUI/PNGという異なる証拠を組み合わせた。ここから言えることを段階に分ける必要がある。

| 証拠 | 支える結論 | 支えない結論 |
| --- | --- | --- |
| compile・link | その構成で実行可能形式を作れる | 実行成功、物理的正しさ |
| 旧新byte一致 | 固定した環境・入力・対象出力の互換性 | 旧式そのものの正しさ、未比較変数・環境 |
| 原値変換一致 | 型・配置・値の保存 | 可視化の適切さ、モデル精度 |
| 年間実行・Restart記録 | その実験の運用成立と時系列 | spin-up十分性、観測一致 |
| GUI・PNG確認 | 記録された操作・描画の成立 | 全画面・platform・現在HEADでの再現 |
| 研究者の意味説明 | 意図・用途・歴史の根拠 | 数値実装の無条件な正しさ |

分析として、比較基準の所在を最初に確かめることが重要だった。VR-0112のように基準がない場合は、実行後に同一性を主張できない。β02では承認したdataset・compiler・precision・並列条件・変数・tolerance・baselineを先に定める必要がある。

## 9. 手戻りから見える設計上の教訓

### 9.1 一般化のしすぎ

Shellの防御的な仕組み、一般的なargument parser、細かすぎるhelper、Map I/Oの対象拡張は、利便性を狙っても科学手順を見えにくくし得た。β01では「手で実行する順序が読める」「詳細検証はconsumer側」という規則が強化された。汎用性の価値は、抽象化の数ではなく、必要な拡張時に既存の意味を保てるかで判断すべきである。

### 9.2 完全性を要求して操作不能にする

Globalの厳密P5/P95要求は、cacheがないとMapを開けない制約になった。研究者が表示用近似を許容するまで、性能問題が機能の利用不能として現れていた。教訓は最初から何でも近似することではなく、統計・背景画像・選択・科学データのどの層で近似を許すかを分けることである。

### 9.3 名前や表示から科学的意味を推定する

同じ `uparea` でも単位が違う、`D2` がrankを示さない、`-10` が物理的な内陸河口と限らない、sample名とInput Matrix名が一致しなくても契約は成立する。これらは横断的な命名整理だけでは直せない。producerとconsumerを往復し、同一性ではなく役割を確認する必要がある。

### 9.4 regionalの成功をglobalへ外挿する

高解像度tileの全面scan、全assignment index、viewport外のCatchment、longitude seamは、小さいMapでは目立たない。COG、bounded native window、cache、Sparse samplingは各々別の問題を解く。性能値もOS cacheや環境に依存し、一回の秒数を一般的な速度保証にしてはいけない。

### 9.5 記録も並行開発に弱い

連番の空きを各作業場所で確認しても、未同期なら同じIDを発行できる。ADR-0013の修復は両方の履歴を残し、branch/commitに依存した旧IDとcanonical IDを対応付けた。一意IDの確保と、後からの参照移行・検証は別問題である。記録validatorの成功も、内容の真実性の保証ではない。

## 10. 四つの研究評価軸から見た到達点

| 軸 | β01で確認できる進展 | 今後必要な評価 |
| --- | --- | --- |
| 知識へのアクセス可能性 | CSV・README・Why手順・KG・catalogから関連根拠へ辿れる構成 | 独立した利用者が対象知識を発見できるか、時間・誤解の比較 |
| 再現性 | sample、年次実行、変換比較、manifest、明示的pathが整備された | 最新fresh cloneと生成packageの同じ受け入れ条件での実行 |
| 拡張性 | I/O責任、registry、共有preprocess、独立scene等の接点が明確化 | 実際の新規変数・新機能追加課題による変更範囲と不具合の評価 |
| ガバナンス | 権限、保存条件、承認、検証境界、記録の区別が文書化された | 適用漏れ、判断待ち、並行開発、外部PRでの運用実績 |

これらは構造上の進展と残課題の整理であり、対照実験の成績ではない。開発期間、commit数、タスク数からAIの速度向上率・コスト削減率・人間の負担軽減率を計算する根拠はない。モデル・token・作業時間・費用の欠測を推計で埋めない。

# 第IV部　β02への示唆とSkills候補

## 11. β02で優先すべきこと

第一に、現在のソースと配布物を同じ受け入れ基準へ結ぶ。ソースcommit、追加データ版・選択、生成manifest、環境、実行条件を固定し、fresh cloneと生成packageの両方から最小実験を実行する。過去のassembly結果やmain統合を代用しない。

第二に、研究者が承認した代表回帰を作る。Binary/NetCDF、連続/Restart、選択したoptional・並列構成のうち、β02で何を支援するかを明示し、比較変数・許容差・保存する基準の由来を決める。科学的変更とI/O・整形変更を別のレビュー単位に保つ。

第三に、metadataを変更した際のconsumer確認を強化する。標準定義を集約した後に変換や可視化の対象発見が抜けた経験から、producer–registry–converter–consumer–documentationの接続を小さく追える手順が必要である。全ファイルを機械的に更新する規則にはしない。

第四に、研究記録は追加量より参照の信頼性を優先する。現行と履歴、確定と提案、当時の検証と現在の検証を分け、並行作業のID確保・統合方法を運用として決める。現在のベータを研究上の比較対象として使うなら、分析対象snapshotと評価課題を先に固定する。

## 12. Skills候補

以下は手順を再利用するための候補であり、この作業ではSkillファイル、実行ツール、`llm_skill/` を作らない。既存の規約を置き換えず、必要な文書を読む順序と受け入れ条件を案内する用途を想定する。優先度P1はβ02の基盤として先行、P2はその後の反復作業向けである。

### S1　科学的保存条件を定めるrefactor review（P1）

目的は、変更対象の主要処理、数値順序、kind、状態、並列、I/O契約を先に特定し、構造・科学・表現変更を分けること。E09・E10の対象縮小、基準不足、Restart分離が根拠となる。材料は [AGENTS.md](../AGENTS.md)、[Fortran設計](../src_main/FORTRAN_DESIGN.md)、[style](../src_main/FORTRAN_STYLE.md)、[preprocessing規約](../docs/preprocessing_code_conventions.md)、VR-0091・0112・0117。一般化できるのは保存条件と証拠の整理手順で、CaMa固有のkind・state・Map/vector・Namelistは参照先として保つ。Skillが科学的変更を承認してはいけない。

### S2　producer–registry–consumer契約の追跡（P1）

目的は単位・次元・record・欠損・特殊値・ID・由来を三方向から照合すること。E03・E18のsentinelとvariant発見漏れが根拠。材料は [metadata仕様](../variable_table/map_metadata_spec.md)、[変数表](../variable_table/README.md)、format conversionのREADME、VR-0196・0197。一般化できるのは契約表と照合順序で、`catmxy`、MPI番号、Fortran Binary record、研究者所有の `workflow_stage` はCaMa固有。未確認項目を推測で埋めない。

### S3　検証計画と証拠の選別（P1）

目的は変更のリスクごとに最小限の意味ある検証を選び、baseline・oracle・環境・未実施を明記すること。E08–E13・E20が根拠。材料はAGENTSのtest原則、[study protocol](study_protocol.md)、代表VR。一般化できるのはcompile、契約、回帰、科学評価の区別で、Mekongや変数別toleranceの承認はCaMa側で必要。依存libraryの再テストやPASS数の最大化を目標にしない。

### S4　配布生成とprovenance review（P1）

目的はread-only sourceと追加データからdry-run、選択、競合確認、staging、manifest、受け入れ実行までの証拠をつなぐこと。E19・E20、clean treeとcommit同一性の限界が根拠。材料は [配布設計](../docs/development_and_distribution_design.md)、[package README](../package/README.md)、VR-0186・0187、KG-0036。一般化できるのは生成物と入力を分ける原則で、採録dataset・ライセンス・版・profileはCaMa固有。パッケージ作成や公開自体は個別の依頼範囲で判断する。

### S5　Scientific Whyの質問と確認済み知識の文書化（P2）

目的は動作と意図を分け、不明点の発見、既存根拠確認、研究者への質問、コメント提案を一貫して行うこと。E03・E05が根拠。材料は既存の [Discovery](../docs/ai_workflows/scientific_why_discovery.md)、[Documentation](../docs/ai_workflows/scientific_why_documentation.md)、[knowledge recovery protocol](analysis/knowledge_recovery_protocol.md)。手順は一般化しやすいが、科学的回答と承認権限は研究者に残す。既存二文書を重複再実装するより、呼出しと適用条件を整える候補である。

### S6　仕様駆動の教材作成と更新（P2）

目的は教育目標、実験仕様、コード・データ制約、実行、図、説明を順に対応付けること。E12・E13の三実験から四実験への変更、manual反復が根拠。材料は [tutorial作成ガイド](../tutorial/how_to_develop_tutorials.md)、[requirements](../tutorial/tutorial_requirements.csv)、各 `tutorial_design.md`、VR-0123・0125。一般化できるのは仕様と実行証拠を先行する方法で、物理構成や学習上の未完成部分は教材固有。未実行の設計を実行済みmanualとして書かない。

### S7　科学的地図表現と大規模GUIの検証（P2）

目的はカテゴリ・連続量、native・Overview、統計母集団、座標、選択geometry、GUI/exportを分けて確認すること。E15–E17が根拠。材料は [figure guideline](../visualization/figure_making_guideline.md)、catalog、Explorer DESIGN、VR-0180・0182–0184。一般化できるのは近似範囲と表示・選択の分離で、nextxy/catmxy、Gallery承認、端点コードはCaMa固有。browser未操作ならGUI確認済みと報告しない。

### S8　履歴に基づく研究記録の統合・回顧（P2）

目的はイベント、タスク、検証、判断、Gitを照合し、同期コミットや欠落証拠を含む履歴を編集すること。E14と本ノートの方法が根拠。材料は [research README](README.md)、[record model ADR](decisions/ADR-0001-record-model.md)、[整合性review](records_integrity_review_20261106.md)、ADR-0013。一般化できるのは証拠階層・事後記録・欠落の明示で、各ID体系はrepository固有。原記録を推定で修正したり、見つからない検証結果を創作したりしない。

## 13. 未確認事項と次の調査

- **β01の正式な公開境界**：今回確認したタグ・Releaseはない。ソースのmain統合は確認したが、公開物の最終版・checksum・配布先の同定は別作業である。
- **最新状態の一貫した実行**：過去のVRを横断して読んだが、最新HEAD全体の再実行や最終packageの受け入れを実施していない。旧時点の成功を補集合のように足して全体PASSとはしない。
- **科学的評価**：承認済み回帰reference、観測・保存則・独立解による評価、spin-up、optional/MPI等の支持範囲には未確定事項がある。SIMDのbugの詳細と同等性・速度も独立した確認対象である。
- **現行の指示と到達点のずれ**：root `AGENTS.md` のTutorial開発節にはTutorial02をillustrative outlineとして扱う古い指示が残る一方、実装・実行と四実験仕様の記録が存在する。新規作業時には対象仕様と承認時点を照合し、この上位案内の更新を別タスクで検討すべきである。本ノートでは既存指示を変更しない。
- **対話の全履歴**：ChatGPT・Codex・研究者の非公開会話を網羅していない。発案者、全代替案、正確な判断日時、AIモデル・費用・人間工数の因果的比較は確定できない。
- **研究記録の欠測**：推定台帳にある過去のVRは回収されたテスト報告ではない。現在の索引の構造整合性と、当時の結果の確実性を区別する。
- **一般化の評価**：Skills候補はβ01の経験から抽出した提案で、他モデルや他研究者に有効と実証したものではない。

## 14. 編集上の自己点検

本文は機能別の到達点、時系列の判断、協働分析、β02提案を分けた。20エピソードは複数DTやコミットを束ねた分析単位であり、作業量の測定値ではない。現在の命名を説明に使いつつ、歴史的資料の旧名は証拠として保持した。特にP3/P97からP5/P95、Logの一律floorから非正下限のみのfallback、NetCDFからCOG表示、GUIのwindow制約、main統合前の記録と統合後の状態を混同しないようにした。

採録は、後続の作業へ影響した設計、意味の回復、再現性、判断・手戻りに重点を置き、日常的な同期・整形・逐一の試行は省略した。重要な未確認事項を成功物語で埋めず、定量的効果を捏造しない。今回の変更はこの内部ノートのみで、既存ログ、設計規約、科学データ、コード、Skill実装は変更しない。
