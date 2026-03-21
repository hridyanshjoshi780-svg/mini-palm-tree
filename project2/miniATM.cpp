#include<iostream>
using namespace std;
float takeout(float account, float withdraw) {
    if (account >= withdraw) {
        account -= withdraw;
        cout << "Withdrawal complete. Amount withdrawn: " << withdraw << endl;
        cout << "Amount left in account: " << account << endl;
    } else {
        cout << "Insufficient funds. Please deposit more money." << endl;
    }
    return account;
}
float moneyin(float account, float deposit) {
    account += deposit;
    cout << "Amount deposited successfully." << endl;
    cout << "Current account balance: " << account << endl;
    return account;
}
int main() {
    float account = 10000.0f;
    float deposit, withdraw;
    char choice;
    const int PIN = 0000; 
    int pinInput;
    const int MAX_ATTEMPTS = 3;
    int attempts = 0;
    bool authenticated = false;
    while (attempts < MAX_ATTEMPTS) {
        cout << "Enter your 4‑digit PIN: ";
        cin >> pinInput;
        if (pinInput == PIN) {
            authenticated = true;
            break;
        }
        attempts++;
        cout << "Incorrect PIN. ";
        if (attempts < MAX_ATTEMPTS) {
            cout << "Please try again." << endl;
        }
    }
    if (!authenticated) {
        cout << "Too many incorrect attempts. Exiting program." << endl;
        return 0; 
    }
    cout << "PIN accepted. Welcome!" << endl;
    do {
        cout << "\nEnter 'w' to withdraw, 'd' to deposit, 'c' to check balance, or 'e' to exit: ";
        cin >> choice;
        switch (choice) {
            case 'w':
                cout << "Enter amount to withdraw: ";
                cin >> withdraw;
                account = takeout(account, withdraw);
                break;
            case 'd':
                cout << "Enter amount to deposit: ";
                cin >> deposit;
                account = moneyin(account, deposit);
                break;
            case 'c':
                cout << "Your account balance is: " << account << endl;
                break;
            case 'e':
                cout << "Exiting the system. Goodbye!" << endl;
                break;
            default:
                cout << "Invalid input. Please try again." << endl;
                break;
        }
    } while (choice != 'e');

    cout<<"thank you for using this game";
    return 0;
}
