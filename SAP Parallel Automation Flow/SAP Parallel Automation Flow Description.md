<img width="1536" height="1024" alt="SAP Parallel Automation Flow" src="https://github.com/user-attachments/assets/7fcf0101-403a-413b-92dc-e5deef91dd3c" />


# Parallel SAP Web Automation for Reporting & Email Distribution

## 🔍 Overview
This project implements a robust, parallel web automation solution designed to extract operational data from SAP/NERP web interfaces, generate Excel reports, and distribute them automatically via email.  
The system leverages asynchronous execution to run multiple SAP transactions concurrently, significantly reducing processing time while maintaining session isolation and reliability.

## 🎯 Objective
To automate the execution of multiple SAP web transactions in parallel, generate structured Excel reports, and deliver them automatically to stakeholders via Outlook—eliminating manual effort, reducing operational delays, and improving reporting consistency.

## 🧠 Methodology
- Implemented **asynchronous task orchestration** using Python’s `asyncio` to execute independent SAP transactions concurrently.
- Each transaction runs in its **own browser and context**, ensuring full session isolation and avoiding authentication conflicts.
- Automated SAP web navigation and interaction using **Playwright**, including:
  - Login handling  
  - Transaction search and menu navigation  
  - Criteria input and execution  
  - Grid interaction and horizontal scrolling  
  - Excel export handling
- Captured browser-based file downloads and saved reports programmatically.
- Integrated **Outlook email automation** to send generated Excel reports automatically once all parallel tasks complete.

## 📊 Key Results
- Reduced total reporting runtime by executing transactions in parallel instead of sequentially.
- Eliminated manual SAP navigation and report exports.
- Delivered fully automated, repeatable Excel reports with zero user intervention.
- Ensured scalability: additional SAP transactions can be added as new parallel flows with minimal changes.
- Improved operational reliability through clear separation of concerns and isolated execution contexts.

## 🛠 Technologies & Skills
- **Python** (Advanced)
- **Async Programming** (`asyncio`, concurrency, task orchestration)
- **Playwright** (Enterprise web automation)
- **SAP / NERP Web Automation**
- **Excel Report Automation**
- **Outlook Integration (pywin32)**
- **Process Automation & RPA Concepts**
- **Enterprise Workflow Design**
- **Error Handling & Timeout Management**

## 🧩 Why This Project Matters
Enterprise systems like SAP are critical but often rely on repetitive, manual processes for reporting.  
This project demonstrates the ability to:
- Design **scalable automation architectures**
- Apply **parallel execution** safely in enterprise environments
- Bridge web automation with business deliverables (Excel + email)
- Deliver **production-ready RPA solutions**, not just scripts

It reflects real-world automation challenges and showcases skills directly applicable to roles in **RPA, Business Process Automation, Data Operations, and Enterprise Systems Engineering**.
