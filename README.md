# Simple ATM CLI Program
A simple C++ command-line ATM simulation that allows users to withdraw, deposit, and check account balance after successful PIN authentication.
 Features
- ✅ 4-digit PIN verification (with 3 attempts limit)
- 💸 Withdraw money
- 💰 Deposit money
- 📊 Check current balance
- 🚪 Exit the system safely
 How It Works
Upon running the program, the user is prompted to enter a 4-digit PIN (default: `0000`).  
If authenticated, they can choose from the following operations:
- `w`: Withdraw an amount
- `d`: Deposit an amount
- `c`: Check current account balance
- `e`: Exit the program
All operations are performed on a simulated account starting with a balance of **₹10,000.00**.
 Usage
 Compilation
To compile the program:
bash
g++ -o atm atm.cpp
