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
boxes.forEach((box) => {
    box.addEventListener("click", () => {
        console.log("box clicked");
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
const showWinner = (winner) =>{
    gamewinner.innerText=`${winner} is winner `;
    gamewinner.classList.remove("hide");
}
const checkwinner = () => {
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