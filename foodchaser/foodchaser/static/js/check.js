function checkState(checkbox)
{
    if (checkbox.checked)
    {
        checkbox.setAttribute("value", "True");
    } else {
    	checkbox.setAttribute("value", "False");
    }
}

function makeCheck()
{
	var inputs = document.getElementsByTagName("input");
	for (i = 0; i < inputs.length; i++) { 
    	input = inputs[i];
    	if(input.getAttribute("type") == "checkbox") {
    		var bool = input.value;
    		if (bool == "True"){
        		input.checked = true;
    		}	
    	}
	}
}