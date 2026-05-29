# Engineering_Practice_Project

工程实践项目《校园信息智能查询智能体》

主要是利用爬虫 + 智能体 + Vue技术栈，在网页端发送给智能体自己的校园账户及密码，实现以下功能：1.自动登录cuit的教务系统；2.在教务系统中查询成绩；3.在教务系统中查询课表；4.在教务系统中查询教室，最终返回给用户相应的查询信息

主要包含以下文件：  
1.前端文件 campus_agent_web：采用Vue搭建，主要包含以下页面：注册、登录、智能体对话

2.后端文件 campus_agent：采用Python搭建，主要包含以下api：智能体功能实现api、前端功能实现api、数据库功能实现api

3.数据库文件 campus_agent_db：采用Mysql构建，主要包含一张表：用户表users

## 前端页面演示：

注册页面：
<img width="1919" height="924" alt="image" src="https://github.com/user-attachments/assets/d830703e-67bd-44ee-88f7-1f9fb5dc46f4" />

登录页面：
<img width="1919" height="919" alt="image" src="https://github.com/user-attachments/assets/457a85ea-f551-4329-8ec7-c4fec7faca7d" />

智能体对话页面：
<img width="1919" height="921" alt="image" src="https://github.com/user-attachments/assets/7f8a3635-cfb2-4a9a-9a73-bee2b96fd784" />

## 具体效果演示：

注册演示：输入自己真实的学校账户及密码
<img width="1919" height="920" alt="image" src="https://github.com/user-attachments/assets/c382983c-0416-4885-b49f-fb1a15cea65d" />

登录演示：输入自己注册过的真实学校账户及密码
<img width="1919" height="922" alt="image" src="https://github.com/user-attachments/assets/623ef3c9-84d6-4983-a043-d1afff1b702b" />

智能体对话演示1：记忆功能
<img width="1919" height="919" alt="image" src="https://github.com/user-attachments/assets/d1db8dd8-18a4-49b0-9fb2-ea501ea0e437" />

智能体对话演示2：课程及教室查询
<img width="1919" height="918" alt="image" src="https://github.com/user-attachments/assets/63d9d008-e93b-4731-bcfa-5020526b1e0b" />

智能体对话演示3：成绩查询
<img width="1919" height="921" alt="image" src="https://github.com/user-attachments/assets/27b76170-c55d-419a-9959-e219a4ae7a00" />
