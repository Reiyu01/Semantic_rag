專案架構:

## .env
能設定模型及qdrant(向量資料庫)端點、資料夾

!!向量資料庫中如Qdrant，會用Collection來分割資料區，若上傳資料進向量資料庫與查詢向量資料庫所用的Collection不同，Agent會告訴你找不到資料!!

## agent.py:
主要Agent中心，利用Semantic Kernel框架來架設AI代理

## plugins/up_to_qdrant.py
會將docs資料夾下的txt檔embedding後儲存進Qdrant
若要上傳資料，請將文件放入docs資料夾後執行 python plugins/up_to_qdrant.py

## plugins/qdrant_plugin.py
AI代理能看到的Plugin工具，此程式檔不需要啟動
當你執行agent.py時，會將plugin列表展示給AI Agent(一併傳入給Agent的還有description)。所以Agent可以藉由description來知道說每個Plugin是做什麼的

接著當一個問題送進來後，若Agent認為該問題可以用什麼工具處理時，就會呼叫該Plugin處理。

Agent ----> Plugin(Function)  

其實就是Agent呼叫Function後，Function返回的值

也可以為Agent掛上其他工具，如連網、返還系統時間 等
也可用多Agent代理系統