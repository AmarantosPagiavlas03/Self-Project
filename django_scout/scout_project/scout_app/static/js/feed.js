document.addEventListener('DOMContentLoaded', function() {
    const feedContainers = document.querySelectorAll('.feed_container');

    feedContainers.forEach(feedContainer => {
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
                    body: JSON.stringify({ liked: !isLiked })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        likeButton.setAttribute('data-liked', !isLiked);
                        likesTotal.textContent = `${data.likes_count.toLocaleString()} likes`;

                        if (!isLiked) {
                            // change to filled heart
                            likeButton.innerHTML = `
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                                    <path fill="currentColor" d="m12 21.35l-1.45-1.32C5.4 15.36 2 12.27 2 8.5C2 5.41 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.08C13.09 3.81 14.76 3 16.5 3C19.58 3 22 5.41 22 8.5c0 3.77-3.4 6.86-8.55 11.53L12 21.35"/>
                                </svg>
                            `;
                        } else {
                            // change to empty heart
                            likeButton.innerHTML = `
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                                    <path fill="currentColor" d="m12.1 18.55l-.1.1l-.11-.1C7.14 14.24 4 11.39 4 8.5C4 6.5 5.5 5 7.5 5c1.54 0 3.04 1 3.57 2.36h1.86C13.46 6 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5c0 2.89-3.14 5.74-7.9 10.05M16.5 3c-1.74 0-3.41.81-4.5 2.08C10.91 3.81 9.24 3 7.5 3C4.42 3 2 5.41 2 8.5c0 3.77 3.4 6.86 8.55 11.53L12 21.35l1.45-1.32C18.6 15.36 22 12.27 22 8.5C22 5.41 19.58 3 16.5 3"/>
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
        const commentForm = feedContainer.querySelector('.add-comment-form form');
        const commentList = feedContainer.querySelector('.feed_container__comments_list');
        const commentCount = feedContainer.querySelector('.feed_container__comments .comment_count');

        if (commentForm && commentList && commentCount) {
            commentForm.addEventListener('submit', function(event) {
                event.preventDefault();
                const postId = commentForm.closest('.add-comment-form').getAttribute('data-post-id');
                const postUrl = commentForm.closest('.add-comment-form').getAttribute('data-post-url');
                const commentInput = commentForm.querySelector('textarea[name="content"]');

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
                    body: JSON.stringify({ content: commentInput.value })
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
                        commentCount.textContent = `${data.comment_count} comments`;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        }
    });
    
});

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