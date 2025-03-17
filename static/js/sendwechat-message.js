/**
 * 发送用户课程信息到指定URL
 * @param {string} userName - 用户姓名
 * @param {number} lessonDuration - 课时时长（分钟）
 * @param {number} remainingTime - 剩余课时时长（分钟）
 * @param {string} targetUrl - 目标URL
 * @returns {Promise} - 返回请求的Promise对象
 */
function sendLessonInfo(userName, lessonDuration, remainingTime, targetUrl) {
  // 获取当前时间
  const currentTime = new Date().toISOString();
  
  // 准备要发送的数据
  const data = {
    userName: userName,
    lessonDuration: lessonDuration,
    remainingTime: remainingTime,
    currentTime: currentTime
  };
  
  // 发送POST请求
  return fetch(targetUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('网络请求失败: ' + response.status);
    }
    return response.json();
  })
  .then(data => {
    console.log('请求成功:', data);
    return data;
  })
  .catch(error => {
    console.error('请求错误:', error);
    throw error;
  });
}

/**
 * 使用示例
 * 
 * // 示例用法:
 * const userName = "张三";
 * const lessonDuration = 60; // 60分钟课时
 * const remainingTime = 240; // 剩余240分钟
 * const targetUrl = "https://example.com/api/lesson-info";
 * 
 * sendLessonInfo(userName, lessonDuration, remainingTime, targetUrl)
 *   .then(response => {
 *     // 处理成功响应
 *   })
 *   .catch(error => {
 *     // 处理错误
 *   });
 */
