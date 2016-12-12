# jbovlaste_otmizer
jbovlaste を OTM-json 形式に変換するスクリプトやその出力結果

``python create_otm_jbovlaste.py [ja/en/jbo/eo/en-simple/...]`` とすると、xml フォルダの ``jbo-XXX-xml.xml`` を json 形式に変換し、それを OTM-json 形式に変換したものを otm-jsonフォルダに保存します。中間体のjson形式は jsonフォルダに保存され、このフォルダ内に該当する json が存在する場合、このjsonを OTM-json 化に利用します。

## 翻訳言語

第1コマンドライン引数は ``create_otm_jbovlaste.py`` 内の ``LANG_LIST`` に依存しています。
言語名は、[jbovlaste](http://jbovlaste.lojban.org/languages.html) の Language Tag に準拠しています。

eg. ``ja``, ``en ja``, ``jbo en ja eo``

## その他コマンド

- ``--zip`` : 生成したOTM-json を圧縮して zip フォルダに保存します。
- ``--nodollar`` : PS定義のプレースホルダの$を消去します。
- ``--addrelations`` : Notesや関連語にある``{}``で囲まれた単語を relations に加えます。単語数によっては処理時間がかなり変わります。``en``で約15秒かかります。

## dependency

- xmltodict

``pip install xmltodict``

ちなみにおかゆの実行環境は Python3.5 です。

## TO DO

- jbovlaste から直接 XML を読み込み、それを OTM-json化する
  - jbovlaste に python からログインしないと xml ﾀﾞｳｿできない（人力の認証が必要となるので）
- 関連語の relations への移行。
  - 日本語辞書では「・関連語：」でまとめられているが、他の辞書では形式が色々あるので統一的にどうこうするのは難しいかもしれない。Notes内の ``{[a-z']+}`` を片っ端から？
- その他もろもろの最適化

## 日本語辞書について

日本語辞書は notes に存在する雑多な項目をすべて独立した項目に変換しています。

- 大意 -> glossword に統合しています。
- 読み方
- 用例（「…／…」の形式の例文）
- 語呂合わせ
- 関連語
