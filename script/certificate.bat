cd D:\QFileTransfer\cer\CA
"..\..\..\Program Files (x86)\OpenSSL-Win64\bin\openssl.exe" req -newkey rsa:2048 -nodes -keyout ca_rsa_private.pem -x509 -days 365 -out ca.crt -subj "/C=CN/ST=GD/L=SZ/O=COM/OU=NSP/CN=CA/emailAddress=782134193@qq.com"

"..\..\..\Program Files (x86)\OpenSSL-Win64\bin\openssl.exe" req -newkey rsa:2048 -nodes -keyout server_rsa_private.pem  -out server.csr -subj "/C=CN/ST=GD/L=SZ/O=COM/OU=NSP/CN=SERVER/emailAddress=782134193@qq.com"
"..\..\..\Program Files (x86)\OpenSSL-Win64\bin\openssl.exe" x509 -req -days 365 -in server.csr -CA ..\CA\ca.crt -CAkey ..\CA\ca_rsa_private.pem -CAcreateserial -out server.crt

"..\..\..\Program Files (x86)\OpenSSL-Win64\bin\openssl.exe" req -newkey rsa:2048 -nodes -keyout client_rsa_private.pem -out client.csr -subj "/C=CN/ST=GD/L=SZ/O=COM/OU=NSP/CN=CLIENT/emailAddress=782134193@qq.com"
"..\..\..\Program Files (x86)\OpenSSL-Win64\bin\openssl.exe" x509 -req -days 365 -in client.csr -CA ..\CA\ca.crt -CAkey ..\CA\ca_rsa_private.pem -CAcreateserial -out client.crt
