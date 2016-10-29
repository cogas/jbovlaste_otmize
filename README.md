# jbovlaste_otmizer
jbovlaste を OTM-json 形式に変換するスクリプトやその出力結果

``python make_jbotm.py [jpn/eng/jbo/epo/all]`` とすると、xml フォルダの ``jbo-XXX-xml.xml`` を json 形式に変換し、それを OTM-json 形式に変換したものを otm-jsonフォルダに保存します。中間体のjson形式は jsonフォルダに保存され、このフォルダ内に該当する json が存在する場合、このjsonを OTM-json 化に利用します。

# TO DO

- jbovlaste から直接 XML を読み込み、それを OTM-json化する
  - jbovlaste に python からログインしないと xml ﾀﾞｳｿできない（人力の認証が必要となるので）
- その他もろもろの最適化

# 日本語辞書について

日本語辞書は notes に存在する雑多な項目をすべて独立した項目に変換しています。

- 大意
- 読み方
- 用例（「…／…」の形式の例文）
- 語呂合わせ
- 関連語
