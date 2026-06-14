# Engineering_Practice_Project

工程实践项目《校园信息智能查询智能体》（面向CUIT）

主要是利用爬虫 + LangGraph智能体 + Vue3的技术栈。实现在登录页面中输入自己的校园账户和密码后，智能体能够根据用户输入的校园账号及密码，实现以下功能：1.自动登录cuit的教务系统；2.在登陆状态下，爬取课表，并且查找相应的实验课，进行拼接，最终返回查询的课表；3.在登陆状态下，爬取成绩表，并且返回查询的成绩表；4.在登陆状态下，爬取考试安排表，并且返回查询的考试安排表

主要包含以下文件：  
1.前端文件 campus_agent_web：基于Vue3搭建，主要包含以下页面：注册、登录、智能体对话

2.前端文件 campus_agent_wx_web：基于微信小程序搭建，主要包含以下页面：注册、登录、智能体对话

3.后端文件 campus_agent：基于爬虫、FastAPI、LangGraph、LangChain搭建，主要包含以下api：智能体功能实现api、前端功能实现api、数据库功能实现api

4.数据库文件 campus_agent_db：基于Mysql搭建，主要包含一张表：用户表users

## 前端页面演示：

注册页面：
<img width="1919" height="924" alt="image" src="https://github.com/user-attachments/assets/d830703e-67bd-44ee-88f7-1f9fb5dc46f4" />

登录页面：
<img width="1919" height="919" alt="image" src="https://github.com/user-attachments/assets/457a85ea-f551-4329-8ec7-c4fec7faca7d" />

智能体对话页面：
<img width="1919" height="918" alt="image" src="https://github.com/user-attachments/assets/3403ec6f-ae0f-49db-9b64-1831a315face" />

## 具体效果演示：

注册演示：输入自己真实的学校账户及密码
<img width="1919" height="920" alt="image" src="https://github.com/user-attachments/assets/c382983c-0416-4885-b49f-fb1a15cea65d" />

登录演示：输入自己注册过的真实学校账户及密码
<img width="1919" height="922" alt="image" src="https://github.com/user-attachments/assets/623ef3c9-84d6-4983-a043-d1afff1b702b" />

智能体对话演示1：记忆功能
<img width="1919" height="919" alt="image" src="https://github.com/user-attachments/assets/d1db8dd8-18a4-49b0-9fb2-ea501ea0e437" />

智能体对话演示2：课程及教室查询
<img width="1919" height="919" alt="image" src="https://github.com/user-attachments/assets/b4abc6b4-8a6d-42e8-a3d9-ed23a2dd7978" />

智能体对话演示3：成绩查询
<img width="1919" height="921" alt="image" src="https://github.com/user-attachments/assets/27b76170-c55d-419a-9959-e219a4ae7a00" />

智能体对话演示4：考试查询
<img width="1919" height="918" alt="image" src="https://github.com/user-attachments/assets/fd1841a8-048b-487e-a223-aa23a9d3667d" />
