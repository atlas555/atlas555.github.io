---
title: 'English FunRoom Study Records'
subtitle: 'Study Records'
author: Sophia
date: 2025-03-17
slug: 'funroom'
show_toc: true
---

<script src="/js/sendwechat-message.js"></script>

<div class="lesson-info-form">
  <div class="form-group">
    <label for="userName">Student Name:</label>
    <input type="text" id="userName" class="form-control" placeholder="Enter student name">
  </div>

  <div class="form-group">
    <label for="lessonDuration">Lesson Duration (minutes):</label>
    <input type="number" id="lessonDuration" class="form-control" placeholder="Enter lesson duration">
  </div>

  <div class="form-group">
    <label for="remainingTime">Remaining Time (minutes):</label>
    <input type="number" id="remainingTime" class="form-control" placeholder="Enter remaining time">
  </div>

  <div class="form-group">
    <label for="targetUrl">Target URL:</label>
    <input type="text" id="targetUrl" class="form-control" placeholder="Enter target URL">
  </div>

  <button onclick="confirmSubmit()" class="btn btn-primary">Submit</button>
</div>

<!-- 确认弹窗 -->
<div id="confirmationModal" class="modal">
  <div class="modal-content">
    <span class="close-button">&times;</span>
    <h3>Confirm Submission</h3>
    <div id="confirmationDetails"></div>
    <div class="modal-buttons">
      <button id="confirmSubmit" class="btn btn-success">Confirm</button>
      <button id="cancelSubmit" class="btn btn-secondary">Cancel</button>
    </div>
  </div>
</div>

<script>
function confirmSubmit() {
  const userName = document.getElementById('userName').value;
  const lessonDuration = parseInt(document.getElementById('lessonDuration').value);
  const remainingTime = parseInt(document.getElementById('remainingTime').value);
  const targetUrl = document.getElementById('targetUrl').value;

  if (!userName || !lessonDuration || !remainingTime || !targetUrl) {
    alert('Please fill in all fields');
    return;
  }

  // 获取当前时间
  const currentTime = new Date().toLocaleString();
  
  // 显示确认弹窗
  const modal = document.getElementById('confirmationModal');
  const detailsContainer = document.getElementById('confirmationDetails');
  
  // 填充确认信息
  detailsContainer.innerHTML = `
    <div class="confirmation-item"><strong>Student Name:</strong> ${userName}</div>
    <div class="confirmation-item"><strong>Lesson Duration:</strong> ${lessonDuration} minutes</div>
    <div class="confirmation-item"><strong>Remaining Time:</strong> ${remainingTime} minutes</div>
    <div class="confirmation-item"><strong>Current Time:</strong> ${currentTime}</div>
    <div class="confirmation-item"><strong>Target URL:</strong> ${targetUrl}</div>
  `;
  
  modal.style.display = 'block';
  
  // 确认按钮事件
  document.getElementById('confirmSubmit').onclick = function() {
    submitLessonInfo();
    modal.style.display = 'none';
  };
  
  // 取消按钮事件
  document.getElementById('cancelSubmit').onclick = function() {
    modal.style.display = 'none';
  };
  
  // 关闭按钮事件
  document.getElementsByClassName('close-button')[0].onclick = function() {
    modal.style.display = 'none';
  };
  
  // 点击弹窗外部关闭
  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = 'none';
    }
  };
}

function submitLessonInfo() {
  const userName = document.getElementById('userName').value;
  const lessonDuration = parseInt(document.getElementById('lessonDuration').value);
  const remainingTime = parseInt(document.getElementById('remainingTime').value);
  const targetUrl = document.getElementById('targetUrl').value;

  sendLessonInfo(userName, lessonDuration, remainingTime, targetUrl)
    .then(response => {
      alert('Information sent successfully!');
    })
    .catch(error => {
      alert('Error sending information: ' + error.message);
    });
}
</script>

<style>
.lesson-info-form {
  max-width: 500px;
  margin: 20px auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-control {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover {
  background-color: #218838;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

/* 弹窗样式 */
.modal {
  display: none;
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0,0,0,0.4);
}

.modal-content {
  background-color: #fefefe;
  margin: 15% auto;
  padding: 20px;
  border: 1px solid #888;
  border-radius: 5px;
  width: 80%;
  max-width: 500px;
}

.close-button {
  color: #aaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
  cursor: pointer;
}

.close-button:hover,
.close-button:focus {
  color: black;
  text-decoration: none;
}

.confirmation-item {
  margin: 10px 0;
  padding: 5px;
  border-bottom: 1px solid #eee;
}

.modal-buttons {
  margin-top: 20px;
  text-align: right;
}

.modal-buttons button {
  margin-left: 10px;
}
</style>
