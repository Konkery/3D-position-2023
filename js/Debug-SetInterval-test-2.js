let prevTime;

const intervalId = setInterval(() => {
  const currentTime = process.hrtime.bigint();
  if (prevTime) {
    const timeDiff = Number(currentTime - prevTime) / 1000000;
    console.log(`Delta time JS: ${timeDiff.toFixed(2)} ms`);
  }
  prevTime = currentTime;
}, 50);

setTimeout(() => {
  console.log('Завершение интервала');
  clearInterval(intervalId);
}, 1000);