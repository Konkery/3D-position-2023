const { performance } = require('perf_hooks');

//let previousTime = performance.now();
let previousTime = Date.now();

const intervalId_start = setInterval(() => {
  const currentTime = Date.now();
  //const currentTime = performance.now();
  const timeDifference = currentTime - previousTime;
  
  let temp_delta = Math.floor(timeDifference * 10000) / 10000;
  console.log(`Delta time: ${temp_delta}`);
  //console.log("Разница времени:", timeDifference, "ms");

  previousTime = currentTime;
}, 25);

const intervalId_stop = setTimeout( ()=>{
    clearInterval(intervalId_start);
},2000);