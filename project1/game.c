#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_INPUT 100

void display_welcome_message() {
    printf("Welcome to the Number Guessing Game!\n");
    printf("I'm thinking of a number between 1 and 100.\n");
    printf("You will be given a number of chances to guess the correct number based on the difficulty level.\n");
}

int select_difficulty(char* difficulty_str) {
    char input[MAX_INPUT];
    int choice;

    printf("\nPlease select the difficulty level:\n");
    printf("1. Easy (10 chances)\n");
    printf("2. Medium (5 chances)\n");
    printf("3. Hard (3 chances)\n");

    while (1) {
        printf("Enter your choice (1, 2, or 3): ");
        fgets(input, sizeof(input), stdin);
        sscanf(input, "%d", &choice);

        if (choice == 1) {
            strcpy(difficulty_str, "easy");
            return 10;
        } else if (choice == 2) {
            strcpy(difficulty_str, "medium");
            return 5;
        } else if (choice == 3) {
            strcpy(difficulty_str, "hard");
            return 3;
        } else {
            printf("Invalid choice. Please select 1, 2, or 3.\n");
        }
    }
}

int get_number_to_guess() {
    return rand() % 100 + 1;
}

int play_game(char* difficulty_str) {
    int chances = select_difficulty(difficulty_str);
    int number_to_guess = get_number_to_guess();
    int attempts = 0;
    char input[MAX_INPUT];
    int guess;

    time_t start_time = time(NULL);

    printf("\nGreat! You have selected the difficulty level with %d chances.\n", chances);
    printf("Let's start the game!\n");

    while (attempts < chances) {
        printf("\nEnter your guess: ");
        fgets(input, sizeof(input), stdin);
        if (sscanf(input, "%d", &guess) != 1) {
            printf("Please enter a valid number.\n");
            continue;
        }

        attempts++;

        if (guess < number_to_guess) {
            printf("Incorrect! The number is greater than %d\n", guess);
        } else if (guess > number_to_guess) {
            printf("Incorrect! The number is less than %d\n", guess);
        } else {
            time_t end_time = time(NULL);
            double elapsed_time = difftime(end_time, start_time);
            printf("Congratulations! You guessed the correct number in %d attempts.\n", attempts);
            printf("Time taken: %.2f seconds.\n", elapsed_time);
            return attempts;
        }
    }

    printf("Sorry, you've run out of chances. The correct number was %d.\n", number_to_guess);
    return attempts;
}

int main() {
    srand(time(NULL));

    int high_scores_easy = 0;
    int high_scores_medium = 0;
    int high_scores_hard = 0;

    char input[MAX_INPUT];
    char difficulty_str[10];

    while (1) {
        display_welcome_message();
        int attempts = play_game(difficulty_str);

        if (strcmp(difficulty_str, "easy") == 0 && 
            (high_scores_easy == 0 || attempts < high_scores_easy)) {
            printf("New high score for Easy difficulty!\n");
            high_scores_easy = attempts;
        } else if (strcmp(difficulty_str, "medium") == 0 && 
                   (high_scores_medium == 0 || attempts < high_scores_medium)) {
            printf("New high score for Medium difficulty!\n");
            high_scores_medium = attempts;
        } else if (strcmp(difficulty_str, "hard") == 0 && 
                   (high_scores_hard == 0 || attempts < high_scores_hard)) {
            printf("New high score for Hard difficulty!\n");
            high_scores_hard = attempts;
        }

        printf("\nCurrent High Scores:\n");
        printf("Easy: %d attempts\n", high_scores_easy);
        printf("Medium: %d attempts\n", high_scores_medium);
        printf("Hard: %d attempts\n", high_scores_hard);

        printf("\nDo you want to play again? (yes or no): ");
        fgets(input, sizeof(input), stdin);
        input[strcspn(input, "\n")] = '\0';

        if (strcmp(input, "yes") != 0 && strcmp(input, "Yes") != 0) {
            printf("Thank you for playing! Goodbye!\n");
            break;
        }
    }

    return 0;
}

