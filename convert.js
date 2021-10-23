var fs = require('fs')
var fromXml = require('./index.js')
// import index.js


//  changes 
// add number attribute for each node increasingly
// name => type 
// breakdown attribbute to subchildren 
// attribute integer for each node 
// DFS to get children id 


var doc = fs.readFileSync('test2.xml')

var tree = fromXml(doc,false)
fs.writeFileSync('test2.json',JSON.stringify(tree))

// console.log(tree)