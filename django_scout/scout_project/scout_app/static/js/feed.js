document.addEventListener('DOMContentLoaded', function() {
    const feedContainers = document.querySelectorAll('.feed_container');

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    feedContainers.forEach(feedContainer => {
        // Expand/collapse comments functionality
        const expandBtn = feedContainer.querySelector('.expand-comments-btn');
        const commentsList = feedContainer.querySelector('.feed_container__comments_list');

        if (expandBtn && commentsList) {
            expandBtn.addEventListener('click', function() {
                if (commentsList.style.display === 'none') {
                    commentsList.style.display = 'block';
                    this.textContent = 'Hide comments';
                    this.classList.add('expanded');
                } else {
                    commentsList.style.display = 'none';
                    this.textContent = `View all ${feedContainer.querySelector('.feed_container__comments_list').children.length} comments`;
                    this.classList.remove('expanded');
                }
            });
        }

        // like button functionality
        const likeButton = feedContainer.querySelector('.feed_container__interactions_like');
        const likesTotal = feedContainer.querySelector('.feed_container__likestotal p');

        if (likeButton && likesTotal) {
            likeButton.addEventListener('click', function() {
                const isLiked = likeButton.getAttribute('data-liked') === 'true';
                const postId = likeButton.getAttribute('data-post-id');
                const postUrl = likeButton.getAttribute('data-post-url');

                if (!postId || !postUrl) {
                    console.error('Post ID or URL not found');
                    return;
                }

                fetch(postUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            liked: !isLiked
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            const newLikedState = !isLiked;
                            likeButton.setAttribute('data-liked', newLikedState);
                            likesTotal.textContent = `${data.likes_count} likes`;

                            if (newLikedState) {
                                // change to filled heart
                                likeButton.innerHTML = `
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="currentColor"/>
                                </svg>
                            `;
                            } else {
                                // change to empty heart
                                likeButton.innerHTML = `
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="none" stroke="currentColor" stroke-width="2"/>
                                </svg>
                            `;
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
            });
        }
        // copy link functionality
        const shareButton = feedContainer.querySelector('.feed_container__interactions_share');
        if (shareButton) {
            const copiedMessage = shareButton.querySelector('.copied-message');

            shareButton.addEventListener('click', function() {
                const postLink = feedContainer.querySelector('.feed_container__image a');

                if (postLink) {
                    // extract post url 
                    const postUrl = postLink.getAttribute('href');
                    const fullPostUrl = `${window.location.origin}${postUrl}`; // construct full url

                    // copy to clipboard
                    navigator.clipboard.writeText(fullPostUrl).then(() => {
                        copiedMessage.style.display = 'block';
                        setTimeout(() => {
                            copiedMessage.style.display = 'none';
                        }, 2000); // hide after 2s
                    });
                }
            });
        }
        // remove excerpt3
        const description = feedContainer.querySelector('.feed_container__description p');
        if (description) {
            description.addEventListener('click', function() {
                this.classList.remove('excerpt3');
            });
        }

        // comment functionality
        const commentForm = feedContainer.querySelector('.comment-form');
        const commentList = feedContainer.querySelector('.feed_container__comments_list');
        const expandCommentsBtn = feedContainer.querySelector('.expand-comments-btn');

        if (commentForm && commentList && expandCommentsBtn) {
            commentForm.addEventListener('submit', function(event) {
                event.preventDefault();
                const postId = commentForm.closest('.add-comment-form').getAttribute('data-post-id');
                const postUrl = commentForm.closest('.add-comment-form').getAttribute('data-post-url');
                const commentInput = commentForm.querySelector('.comment-input');

                if (!postId || !postUrl || !commentInput) {
                    console.error('Post ID, URL, or comment input not found');
                    return;
                }

                fetch(postUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            content: commentInput.value
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            const newComment = document.createElement('div');
                            newComment.classList.add('feed_container__comments_list_comment');
                            newComment.innerHTML = `
                            <p><b>${data.author}</b>: ${data.comment}</p>
                        `;
                            commentList.appendChild(newComment);
                            commentInput.value = '';
                            expandCommentsBtn.textContent = `View all ${data.comment_count} comments`;
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
            });
        }

        // Delete comment functionality
        if (commentsList) {
            commentsList.addEventListener('click', function(event) {
                const deleteBtn = event.target.closest('.delete-comment-btn');
                if (!deleteBtn) return;

                const commentId = deleteBtn.dataset.commentId;
                const deleteUrl = deleteBtn.dataset.deleteUrl;
                const commentElement = deleteBtn.closest('.feed_container__comments_list_comment');

                fetch(deleteUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            commentElement.remove();
                            if (expandCommentsBtn) {
                                if (data.comment_count > 0) {
                                    expandCommentsBtn.textContent = `View all ${data.comment_count} comments`;
                                } else {
                                    expandCommentsBtn.style.display = 'none'; // hide the button if no comments
                                }
                            }
                        } else {
                            alert(data.error || 'Error deleting comment');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Error deleting comment');
                    });
            });
        }
    });

});