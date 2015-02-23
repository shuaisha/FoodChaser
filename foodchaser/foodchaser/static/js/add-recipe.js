// Creating an instruction form
function addStep() {
    // Get table of steps
    var steps = document.getElementById("step-table");
    var numRows = steps.rows.length;
    var row = steps.insertRow(numRows);
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    var cell3 = row.insertCell(2);
    var cell4 = row.insertCell(3);
    cell1.innerHTML = "<input class='form-control' maxlength='200' name='text" + numRows + "' type='text' placeholder='Step'/>";
    cell2.innerHTML = "<input class='form-control' max='60' min='0' name='preptime" + numRows + "' placeholder='0' type='number' />";
    cell3.innerHTML = "<input class='form-control' max='60' min='0' name='cooktime" + numRows + "' placeholder='0' type='number' />";
    cell4.innerHTML = "<input type='file' name='picture" + numRows + "' class='btn btn-success'>";
}

// Creating an ingredient form
function addIngredient() {
    // Get table of steps
    var steps = document.getElementById("ingredient-table");
    var numRows = steps.rows.length;
    var row = steps.insertRow(numRows);
    var cell1 = row.insertCell(0);
    cell1.id = 'prefetch'+numRows
    var cell2 = row.insertCell(1);
    var cell3 = row.insertCell(2);
    var cell4 = row.insertCell(3);
    cell1.innerHTML = "<input class='form-control typeahead" + numRows + "' maxlength='20' name='name" + numRows + "' placeholder='Item' type='text' />";
    cell2.innerHTML = "<input class='form-control' min='0' name='quantity" + numRows + "' type='number' placeholder='0'/>";
    cell3.innerHTML = "<input class='form-control' maxlength='20' name='unit" + numRows + "' type='text' placeholder='Unit'/>";
    cell4.innerHTML = "<input class='form-control' maxlength='200' name='notes" + numRows + "' type='text' placeholder='Notes'/>";
    var ingredients = new Bloodhound({
  datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
  queryTokenizer: Bloodhound.tokenizers.whitespace,
  limit: 10,
  prefetch: {
    // url points to a json file that contains an array of country names, see
    // https://github.com/twitter/typeahead.js/blob/gh-pages/data/countries.json
    url: 'https://s3.amazonaws.com/15437recipehub/static/ingredients.json',
    // the json file contains an array of strings, but the Bloodhound
    // suggestion engine expects JavaScript objects so this converts all of
    // those strings
    filter: function(list) {
      return $.map(list, function(ingredients) { return { name: ingredients }; });
    }
  }
});
 
// kicks off the loading/processing of `local` and `prefetch`
ingredients.initialize();
 
// passing in `null` for the `options` arguments will result in the default
// options being used
$('#prefetch'+numRows+' .typeahead'+numRows).typeahead(null, {
  name: 'ingredients',
  displayKey: 'name',
  // `ttAdapter` wraps the suggestion engine in an adapter that
  // is compatible with the typeahead jQuery plugin
  source: ingredients.ttAdapter()
});
}
