const errorBox = document.getElementById("login-error-box");
const usernameInput = document.getElementById("i-username");
const btnSession = document.getElementById("btn-start-session");

const popError = (error) =>{
    errorBox.innerText = error
    errorBox.style.animation = "login_errorbox_open .4s linear forwards"
}

const closeError = () =>{
    errorBox.style.animation = "login_errorbox_close .4s linear forwards"
}

btnSession.onclick = () => {
    closeError()
    const xhttp = new XMLHttpRequest
    xhttp.open("POST", "/api/login", true)
    xhttp.setRequestHeader("Content-type", "application/json")
    xhttp.send(JSON.stringify({username: usernameInput.value}))
    xhttp.onreadystatechange = (data) => {
        if (data.target.readyState == 4 && data.target.status == 200){
            window.location.href = "/panel";
        }else{
            popError(JSON.parse(data.target.responseText).message)
            console.log(data)
        }
    }
}
