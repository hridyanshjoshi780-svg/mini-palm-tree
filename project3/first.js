let boxes = document.querySelectorAll(".gamebox");
let resetbox = document.querySelector("#gamereset");
let newgame = document.querySelector("#newgame");
let gamewinner = document.querySelector(".winner");
let playerO = true; //playerX and playerO with alternate turns
const winPattern = [
    [0,1,2],
    [0,3,6],
    [0,4,8],
    [1,4,7],
    [2,5,8],
    [2,4,6],
    [3,4,5],
    [6,7,8]
];
const resetGame = () => { //this function is being used to restart the game 
    playerO = true;
    enablegame();
    gamewinner.classList.add("hide");
}
boxes.forEach((box) => { //this function is being used to play alternately
    box.addEventListener("click", () => {
        if(playerO === true){ //playerO turn
            playerO= false;
            box.innerText="O";
        }else{ //playerX turn
            box.innerText="X"
            playerO= true;
        }
        box.disabled=true;
        checkwinner();
    })
})
const disablegame = () =>{ // this function is used to disable the buttons of game after one player has won
    for(let box of boxes){
        box.disabled = true;
    }
}
const showWinner = (winner) =>{ // this function is used to display the winning message 
    gamewinner.innerText=`${winner} is winner `;
    gamewinner.classList.remove("hide");
    disablegame();
}
const enablegame = () => { //this function is in used after hitting restart to empty the boxes and return to the initial player
    for(let box of boxes){
        box.disabled = false;
        box.innerText = " ";
    }
}
const checkwinner = () => { // this functions checks the winning conditions based on the patterns 
    for(pattern of winPattern){
        let pos1 = boxes[pattern[0]].innerText;
        let pos2 = boxes[pattern[1]].innerText;
        let pos3 = boxes[pattern[2]].innerText;
        if(pos1 != "" && pos2 != "" && pos3 != ""){
            if(pos1 === pos2 && pos2 === pos3){
                showWinner(pos1);
            }
        }
    }
}
newgame.addEventListener("click", resetGame);
resetbox.addEventListener("click", resetGame);