# Практика 6. Транспортный уровень

## Wireshark: UDP (5 баллов)
Начните захват пакетов в приложении Wireshark и затем сделайте так, чтобы ваш хост отправил и
получил несколько UDP-пакетов (например, с помощью обращений DNS).
Выберите один из UDP-пакетов и разверните поля UDP в окне деталей заголовка пакета.
Ответьте на вопросы ниже, представив соответствующие скрины программы Wireshark.

#### Вопросы
![udp1.jpg](screenshoots%2Fudp%2Fudp1.jpg)
1. Выберите один UDP-пакет. По этому пакету определите, сколько полей содержит UDP-заголовок.
   - 4 поля
2. Определите длину (в байтах) для каждого поля UDP-заголовка, обращаясь к отображаемой
   информации о содержимом полей в данном пакете.
   - По 2 байта (слева снизу на скрине Wireshark подписывает)
3. Значение в поле Length (Длина) – это длина чего?
   - Нажимаем по этому полю и видим слева снизу подпись, что это длина описания udp-протокола, выраженная в октетах(байтах), 
   включая хедеры и полезную нагрузку, наглядно это подтверждается тем, что 41(payload на фото)+8(все поля)=49(udp.length)
4. Какое максимальное количество байт может быть включено в полезную нагрузку UDP-пакета?
   - Поле для длины всего пакета двухбайтовое(16 бит), значит максимальная длина $2^{16}-1 = 65535$, 
   из длины вычтем заголовки и байты под IP(20 байт): значит ответ на вопрос не превосходит $65535 - 8 - 20 = 65507$
5. Чему равно максимально возможное значение номера порта отправителя?
   - Поле для порта отправителя двухбайтовое(16 бит), значит $2^{16}-1 = 65535$

6. Какой номер протокола для протокола UDP? Дайте ответ и для шестнадцатеричной и
   десятеричной системы. Чтобы ответить на этот вопрос, вам необходимо заглянуть в поле
   Протокол в IP-дейтаграмме, содержащей UDP-сегмент.
   - 17(десятиричное) можно увидеть слева ```Protocol: UDP (17)```, 
   - 11(шестанднадцатиричное) соответствующее можно увидеть справа
   
![udp2.jpg](screenshoots%2Fudp%2Fudp2.jpg)
7. Проверьте UDP-пакет и ответный UDP-пакет, отправляемый вашим хостом. Определите
   отношение между номерами портов в двух пакетах.
   - В первом пакете номера портов ```Src Port: 49484, Dst Port: 53```, в ответном поменяны местами: ```Src Port: 53, Dst Port: 49484``` 

![udp3.jpg](screenshoots%2Fudp%2Fudp3.jpg)


   
## Программирование. FTP

### FileZilla сервер и клиент (3 балла)
1. Установите сервер и клиент [FileZilla](https://filezilla.ru/get)
2. Создайте FTP сервер. Например, по адресу 127.0.0.1 и портом 21. 
   Укажите директорию по умолчанию для работы с файлами.
3. Создайте пользователя TestUser. Для простоты и удобства можете отключить использование сертификатов.
4. Запустите FileZilla клиента (GUI) и попробуйте поработать с файлами (создать папки,
добавить/удалить файлы).

Приложите скриншоты.

#### Скрины
1. После всех установок запускаем FileZilla server, нажимаем configure

![filezilla1.jpg](screenshoots%2Ffilezilla%2Ffilezilla1.jpg)

2. Убеждаемся, что слушаем на порте 21

![filezilla2.jpg](screenshoots%2Ffilezilla%2Ffilezilla2.jpg)

3. Переходим в Users, добавляем TestUser: для этого нажимаем кнопку ```Add``` в столбце ```Available users```,
затем монтируем пути: нажимаем ```Add``` в ```mount points``` и вводим к чему хотим дать доступ. Сохраняем конфиг

![filezilla3.jpg](screenshoots%2Ffilezilla%2Ffilezilla3.jpg)

4. Запускаем FileZilla client, переходим в ```Файл > Менеджер сайтов```

![filezilla4.jpg](screenshoots%2Ffilezilla%2Ffilezilla4.jpg)

5. Нажимаем ```новый сайт```, вводим хост, вводим порт, вводим пользователя в режиме интерактив, 
нажимаем ```соединиться```

![filezilla5.jpg](screenshoots%2Ffilezilla%2Ffilezilla5.jpg)

6. Видим удаленный сайт с ожидаемым каталогом, снизу видим, что там лежит заранее заготовленный файл ```Test.txt```

![filezilla6.jpg](screenshoots%2Ffilezilla%2Ffilezilla6.jpg)

7. С помощью правой кнопки мыши можем создавать каталоги/файлы/редактировать файлы

![filezilla7.jpg](screenshoots%2Ffilezilla%2Ffilezilla7.jpg)
![filezilla8.jpg](screenshoots%2Ffilezilla%2Ffilezilla8.jpg)
![filezilla9.jpg](screenshoots%2Ffilezilla%2Ffilezilla9.jpg)

### FTP клиент (3 балла)
Создайте консольное приложение FTP клиента для работы с файлами по FTP. Приложение может
обращаться к FTP серверу, созданному в предыдущем задании, либо к какому-либо другому серверу 
(есть много публичных ftp-серверов для тестирования, [вот](https://dlptest.com/ftp-test/) один из них).

Приложение должно:
- Получать список всех директорий и файлов сервера и выводить его на консоль
- Загружать новый файл на сервер
- Загружать файл с сервера и сохранять его локально

Бонус: Не используйте готовые библиотеки для работы с FTP (например, ftplib для Python), а реализуйте решение на сокетах **(+3 балла)**.

#### Демонстрация работы
У меня простой вариант: ftplib для Python + FileZilla Server, убедимся, что всё работает
1. Сначала видим, что в директории ```C:\Users\serge\networks-course\lab06\server``` (её как и ранее использую как хранилище
для данных сервера) нет файла ```Example.txt``` 
(его я планирую передать с помощью запуска своего python client), но есть файл ```Test.txt``` (его я планирую скачать
с помощью клиента). 

![1.jpg](screenshoots%2Fpython_FTP_client%2F1.jpg)

2. Изначально у меня в директории со скриптом нет кроме него ничего, но как видно со скрина, 
я создаю FTP-соединение, вывожу в консоль все файлы с удаленного сервера, а уже затем создаю хранилище ```store```,
где буду хранить файлы для клиента. Запустим же скрипт! :)

![2.jpg](screenshoots%2Fpython_FTP_client%2F2.jpg)

3. После запуска скрипта у меня появилось два файла в ```store``` один ```Test.txt``` -- его удалось скачать,
другой ```Example.txt``` -- его мы создали сами, он должен загрузиться на сервер.

![3.jpg](screenshoots%2Fpython_FTP_client%2F3.jpg)

4. Посмотрим что вывелось в лог: видим, что файлы и каталоги с сервера вывелись все. Более того, после загрузки файла
на сервер там теперь на один файл больше, так что это успех, всё работает. 

![4.jpg](screenshoots%2Fpython_FTP_client%2F4.jpg)

5. Можно даже открыть хранилище сервера и увидеть этот файл там, хотя по пункту 4 и так это было понятно.

![5.jpg](screenshoots%2Fpython_FTP_client%2F5.jpg)

### GUI FTP клиент (4 балла)
Реализуйте приложение FTP клиента с графическим интерфейсом. НЕ используйте C#.

Возможный интерфейс:

<img src="images/example-ftp-gui.png" width=300 />

В приложении должна быть поддержана следующая функциональность:
- Выбор сервера с указанием порта, логин и пароль пользователя и возможность
подключиться к серверу. При подключении на экран выводится список всех доступных
файлов и директорий
- Поддержаны CRUD операции для работы с файлами. Имя файла можно задавать из
интерфейса. При создании нового файла или обновлении старого должно открываться
окно, в котором можно редактировать содержимое файла. При команде Retrieve
содержимое файла можно выводить в главном окне.

#### Демонстрация работы
todo

### FTP сервер (5 баллов)
Реализуйте свой FTP сервер, который работает поверх TCP сокетов. Вы можете использовать FTP клиента, реализованного на прошлом этапе, для тестирования своего сервера.
Сервер должен реализовать возможность авторизации (с указанием логина/пароля) и поддерживать команды:
- CWD
- PWD
- PORT
- NLST
- RETR
- STOR
- QUIT

#### Демонстрация работы
todo
