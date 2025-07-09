# AugmentCode-Free
AugmentCode无限免费续杯方案；新账号可获得600次免费的Claude Sonnet 4调用


2025年6月18日更新：

最新思路：

team邀请方式：

1.首先准备任意一个账号（被封禁的，试用到期的，用完免费次数的都可以），浏览器打开https://app.augmentcode.com/account/subscription
获取个人中心页面，点击Team，再点击add member添加一个小号作为团队成员。
![image](https://github.com/user-attachments/assets/caa0f8dc-d189-476f-bc3f-84ee0037e03b)


2.这个小号可以用域名邮箱，随意。添加到团队里面后会收到一封激活邮件。
![image](https://github.com/user-attachments/assets/63117ef9-1e9c-4641-99c1-9d3c9f56f435)


3.点击邮件链接https://auth.augmentcode.com/invitations   ，用小号登录激活。按照提示走完流程即可。

4.执行下面的脚本清理本地环境配置，清理完毕后登录刚刚的小号。然后就可以稳定使用了，到目前为止，方法仍然有效。

总结：大号随便什么号，封了的都可以，大号创建team拉小号，小号就可以无限用，注意一定要小号登录augment插件，登录前记得执行清理脚本。

---


# AugmentCode-Free
AugmentCode unlimited free refill plan; new accounts can get 600 free Claude Sonnet 4 calls

Updated on June 18, 2025:

Latest ideas:

Team invitation method:

1. First prepare any account (banned, trial expired, or used up free times), open https://app.augmentcode.com/account/subscription in the browser
Get the personal center page, click Team, and then click add member to add a small account as a team member.
![image](https://github.com/user-attachments/assets/caa0f8dc-d189-476f-bc3f-84ee0037e03b)

2. This small account can use a domain name email, as you like. You will receive an activation email after adding it to the team.
![image](https://github.com/user-attachments/assets/63117ef9-1e9c-4641-99c1-9d3c9f56f435)

3. Click the email link https://auth.augmentcode.com/invitations and log in with the secondary account to activate. Follow the prompts to complete the process.

4. Execute the following script to clean up the local environment configuration, and log in to the secondary account just now after cleaning. Then you can use it stably. So far, the method is still effective.

Summary: The primary account can be any account, even if it is blocked. The primary account can create a team and pull the secondary account, and the secondary account can be used unlimitedly. Note that you must log in to the augmentation plug-in with the secondary account, and remember to execute the cleanup script before logging in.

---

<p align="center">
  <a href="#english">English</a> | <a href="#中文">中文</a>
</p>

---

<a name="english"></a>

# AugmentCode-Free (English)

**AugmentCode-Free** is a Python-based toolkit, now featuring a modern **Graphical User Interface (GUI)** alongside its command-line interface. It's designed to provide maintenance and tweaking utilities for VS Code, helping users manage aspects like telemetry and local cache.

## Features

### Core Functionality (Available in CLI & GUI)
-   **VS Code Database Cleaning**: Cleans specific entries from VS Code's local databases.
-   **VS Code Telemetry ID Modification**: Helps in resetting or changing telemetry identifiers stored by VS Code.

### New GUI Features
-   **Intuitive Interface**: A user-friendly graphical alternative to command-line operations.
-   **One-Click Operations**: Easily perform tasks like modifying VS Code telemetry IDs and cleaning VS Code databases with a single click.
-   **Process Management**: Automatically detects and offers to close running VS Code instances to ensure operations proceed smoothly.
-   **User Feedback**: Provides clear confirmation dialogs and status messages for all operations.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/BasicProtein/AugmentCode-Free.git](https://github.com/BasicProtein/AugmentCode-Free.git)
    cd AugmentCode-Free
    ```
2.  **Install dependencies (if any specified in `requirements.txt` or `setup.py`):**
    ```bash
    pip install .
    # or
    # pip install -r requirements.txt
    ```

## Usage

**Notes**:
- Please log out of your AugmentCode account before use
- Close the IDE background and run the script

**Notes**:
- Please log out of your AugmentCode account before use
- Close the IDE background and run the script

**Notes**:
- Please log out of your AugmentCode account before use
- Close the IDE background and run the script

**(Important things should be said three times!)**

You can use AugmentCode-Free in two ways:

### 1. Graphical User Interface (GUI) - Recommended
The GUI provides an easy-to-use interface for all features.

-   **Directly (from project root):**
    ```bash
    python main.py
    ```

-   **If installed via pip (as `augment-tools-gui`):**
    ```bash
    augment-tools-gui
    ```

### 2. Command-Line Interface (CLI)
For users who prefer the command line or need to script operations.

-   **If installed via pip (as `augment-tools`):**
    ```bash
    augment-tools --help
    ```
    (Follow on-screen instructions for specific commands like `clean-db` or `modify-telemetry`)

-   **Directly (for development/advanced use, from project root):**
    Refer to `augment_tools_core/cli.py` for direct script execution details if needed.

## Disclaimer
Use these tools at your own risk. Always back up important data before running maintenance functions, especially when they modify application files. While backups might be created automatically by some functions, caution is advised.

---

<a name="中文"></a>

# AugmentCode-Free (中文)

**AugmentCode-Free** 是一个基于 Python 的工具包，现已配备现代化的**图形用户界面 (GUI)** 以及原有的命令行界面。它旨在为 VS Code 提供维护和调整实用程序，帮助用户管理遥测数据和本地缓存等方面。

## 功能特性

###核心功能 (命令行及GUI均可用)
-   **VS Code 数据库清理**: 清理 VS Code 本地数据库中的特定条目。
-   **VS Code 遥测ID修改**: 帮助重置或更改 VS Code 存储的遥测标识符。

### 全新 GUI 特性
-   **直观界面**: 提供用户友好的图形操作界面，作为命令行的替代选择。
-   **一键式操作**: 通过单击即可轻松执行修改 VS Code 遥测ID、清理 VS Code 数据库等任务。
-   **进程管理**: 自动检测并提示关闭正在运行的 VS Code 实例，以确保操作顺利进行。
-   **用户反馈**: 为所有操作提供清晰的确认对话框和状态消息。

## 安装

1.  **克隆仓库:**
    ```bash
    git clone [https://github.com/BasicProtein/AugmentCode-Free.git](https://github.com/BasicProtein/AugmentCode-Free.git)
    cd AugmentCode-Free
    ```
2.  **安装依赖 (如果 `requirements.txt` 或 `setup.py` 中有指定):**
    ```bash
    pip install .
    # 或者
    # pip install -r requirements.txt
    ```

## 使用方法

**注意事项**：
 - 使用前请确保退出AugmentCode账号的登录
 - 关闭IDE后台再运行脚本

**注意事项**：
 - 使用前请确保退出AugmentCode账号的登录
 - 关闭IDE后台再运行脚本

**注意事项**：
 - 使用前请确保退出AugmentCode账号的登录
 - 关闭IDE后台再运行脚本

**（重要的事情说三遍！）**

您可以通过两种方式使用 AugmentCode-Free：

### 1. 图形用户界面 (GUI) - 推荐
GUI 为所有功能提供了简单易用的操作界面。

-   **直接运行 (从项目根目录):**
    ```bash
    python main.py
    ```

-   **如果通过 pip 安装 (作为 `augment-tools-gui`):**
    ```bash
    augment-tools-gui
    ```

### 2. 命令行界面 (CLI)
适用于喜欢命令行或需要编写脚本自动执行操作的用户。

-   **如果通过 pip 安装 (作为 `augment-tools`):**
    ```bash
    augment-tools --help
    ```
    (根据屏幕提示执行具体命令，如 `clean-db` 或 `modify-telemetry`)

-   **直接运行 (用于开发/高级用户, 从项目根目录):**
    如果需要，请参考 `augment_tools_core/cli.py` 了解直接执行脚本的详细信息。

## 免责声明
请自行承担使用这些工具的风险。在运行维护功能前，请务必备份重要数据，尤其是在它们修改应用程序文件时。虽然某些功能可能会自动创建备份，但仍建议谨慎操作。
