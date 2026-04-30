document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-btn');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const fileId = this.getAttribute('data-id');
            const row = this.closest('tr');

            if (confirm('Вы уверены, что хотите удалить этот файл?')) {
                fetch(`/api/files/${fileId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (response.ok) {
                        row.remove();
                        if (document.querySelectorAll('tbody tr').length === 0) {
                        }
                    } else {
                        alert('Ошибка при удалении файла.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Произошла ошибка сети.');
                });
            }
        });
    });
});