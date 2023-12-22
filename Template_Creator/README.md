# LE SSM Wrapper Template Creator
An internal GUI tool that will improve the accuracy and efficiency to run scripts across the ST fleet for Lawson.​

## How to Use?
1. Fill up the required options (**Path of Created Script, SSM Wrapper Location, Accounts**).

2. For the other entities, you may or may not fill up them as they are optional.

3. Customize the headers of your script to be created by clicking "**Edit Headers**" before choosing what action you want to do.

4. Choose an action.
- **Create Template** - creates the ps1 template based on the values set that is ready to be executed. After execution, you will have the option to view the powershell file.
- **Create and Run Template** - creates the ps1 template based on the values set and will be executed. After execution. you will have the option to view the report or the powershell file.
- **Create and Run Template (WhatIf)** - creates the ps1 template based on the values set and will be executed with -WhatIf enabled. After execution. you will have the option to view the report or the powershell file.
- **Import CSV** - gives you the option to import a CSV file which you produced from the first output of your script. The CSV file usually contains the machines with failed results. Instance IDs with their respective account and region will be parsed and be used on the new script.

## Note
- The created file will be stored in the same directory of the application if Output location does not have a value.
- This tool only allows one process at a time.

© 2021 Clark Pañares.