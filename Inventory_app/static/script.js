// Enhanced Inventory Management JavaScript

// Pagination and Virtual Scrolling
let currentPage = 1;
const itemsPerPage = 50;

function paginateTable(tableId, page = 1) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const totalRows = rows.length;
    const totalPages = Math.ceil(totalRows / itemsPerPage);
    
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    
    rows.forEach((row, index) => {
        row.style.display = (index >= startIndex && index < endIndex) ? '' : 'none';
    });
    
    updatePaginationControls(tableId, page, totalPages);
}

function updatePaginationControls(tableId, currentPage, totalPages) {
    let paginationDiv = document.getElementById(tableId + '_pagination');
    if (!paginationDiv) {
        paginationDiv = document.createElement('div');
        paginationDiv.id = tableId + '_pagination';
        paginationDiv.className = 'pagination-controls';
        document.getElementById(tableId).parentNode.appendChild(paginationDiv);
    }
    
    let html = `<div style="display: flex; justify-content: center; align-items: center; gap: 10px; margin: 10px 0;">`;
    
    if (currentPage > 1) {
        html += `<button class="btn btn-sm btn-primary" onclick="paginateTable('${tableId}', ${currentPage - 1})">Previous</button>`;
    }
    
    html += `<span>Page ${currentPage} of ${totalPages}</span>`;
    
    if (currentPage < totalPages) {
        html += `<button class="btn btn-sm btn-primary" onclick="paginateTable('${tableId}', ${currentPage + 1})">Next</button>`;
    }
    
    html += `</div>`;
    paginationDiv.innerHTML = html;
}

// Modal Functions
function editItem(id, serial, itemName, itemType, admin, createdAt, unitsImported, unitsInstalled, unitsAvailable) {
    document.getElementById('editSerial').value = serial || '';
    document.getElementById('editItemName').value = itemName || '';
    document.getElementById('editItemType').value = itemType || 'conversion_kit';
    document.getElementById('editAdmin').value = admin || '';
    
    // Handle created_at field if it exists
    const createdAtField = document.getElementById('editCreatedAt');
    if (createdAtField) {
        createdAtField.value = createdAt || '';
    }
    
    document.getElementById('editUnitsImported').value = unitsImported || 0;
    document.getElementById('editUnitsInstalled').value = unitsInstalled || 0;
    document.getElementById('editUnitsAvailable').value = unitsAvailable || 0;
    document.getElementById('updateForm').action = '/update_item/' + id;
    document.getElementById('editModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('editModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    const returnModal = document.getElementById('returnStatusModal');
    if (event.target === modal) {
        closeModal();
    }
    if (event.target === returnModal) {
        closeReturnModal();
    }
}

// Table Search and Filter Functions
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length; j++) {
            if (cells[j].textContent.toLowerCase().includes(filter)) {
                found = true;
                break;
            }
        }
        
        rows[i].style.display = found ? '' : 'none';
    }
}

// Form Validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#dc3545';
            isValid = false;
        } else {
            input.style.borderColor = '#ced4da';
        }
    });
    
    return isValid;
}

// Auto-calculate available units
function calculateAvailable() {
    const imported = parseInt(document.getElementById('editUnitsImported').value) || 0;
    const installed = parseInt(document.getElementById('editUnitsInstalled').value) || 0;
    const available = Math.max(0, imported - installed);
    document.getElementById('editUnitsAvailable').value = available;
}

// Add event listeners when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add auto-calculation for available units
    const importedInput = document.getElementById('editUnitsImported');
    const installedInput = document.getElementById('editUnitsInstalled');
    
    if (importedInput && installedInput) {
        importedInput.addEventListener('input', calculateAvailable);
        installedInput.addEventListener('input', calculateAvailable);
    }
    
    // Add confirmation for delete actions
    const deleteLinks = document.querySelectorAll('a[href*="delete"]');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Initialize pagination for large tables
    const tables = document.querySelectorAll('table[id]');
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        if (rows.length > itemsPerPage) {
            paginateTable(table.id, 1);
        }
    });
    
    // Add smooth scrolling
    document.querySelectorAll('.scrollable-content').forEach(element => {
        element.style.scrollBehavior = 'smooth';
    });
});

// Dropdown Toggle Functions
function toggleDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    const arrow = dropdown.parentElement.querySelector('.dropdown-arrow');
    const isVisible = dropdown.style.display === 'block';
    
    // Close all other dropdowns first
    document.querySelectorAll('.dropdown-content').forEach(dd => {
        if (dd.id !== dropdownId) {
            dd.style.display = 'none';
            const otherArrow = dd.parentElement.querySelector('.dropdown-arrow');
            if (otherArrow) otherArrow.classList.remove('rotated');
        }
    });
    
    dropdown.style.display = isVisible ? 'none' : 'block';
    
    // Toggle arrow rotation
    if (arrow) {
        arrow.classList.toggle('rotated', !isVisible);
    }
    
    // Add animation
    if (!isVisible) {
        dropdown.style.opacity = '0';
        dropdown.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            dropdown.style.opacity = '1';
            dropdown.style.transform = 'translateY(0)';
        }, 10);
    }
}

// Return Status Management
function updateReturnStatus(returnId, currentStatus, currentNotes) {
    document.getElementById('returnStatus').value = currentStatus;
    document.getElementById('returnNotes').value = currentNotes;
    document.getElementById('returnStatusForm').action = '/update_return_status/' + returnId;
    document.getElementById('returnStatusModal').style.display = 'block';
}

function closeReturnModal() {
    document.getElementById('returnStatusModal').style.display = 'none';
}

// Edit Return Functions
function editReturn(id, date, itemSerial, personnel, status, notes) {
    document.getElementById('editReturnDate').value = date || '';
    document.getElementById('editItemSerial').value = itemSerial || '';
    document.getElementById('editPersonnel').value = personnel || '';
    document.getElementById('editStatus').value = status || 'pending';
    document.getElementById('editNotes').value = notes || '';
    document.getElementById('editReturnForm').action = '/update_return/' + id;
    document.getElementById('editReturnModal').style.display = 'block';
}

function closeEditReturnModal() {
    document.getElementById('editReturnModal').style.display = 'none';
}

// Edit Replacement Functions
function editReplacement(id, date, oldSerial, newSerial, riderName, riderNumber, station) {
    document.getElementById('editReplacementDate').value = date || '';
    document.getElementById('editOldSerial').value = oldSerial || '';
    document.getElementById('editNewSerial').value = newSerial || '';
    document.getElementById('editReplacementRiderName').value = riderName || '';
    document.getElementById('editReplacementRiderNumber').value = riderNumber || '';
    document.getElementById('editReplacementStation').value = station || '';
    document.getElementById('editReplacementForm').action = '/update_replacement/' + id;
    document.getElementById('editReplacementModal').style.display = 'block';
}

function closeEditReplacementModal() {
    document.getElementById('editReplacementModal').style.display = 'none';
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    const returnModal = document.getElementById('returnStatusModal');
    const editReturnModal = document.getElementById('editReturnModal');
    const editReplacementModal = document.getElementById('editReplacementModal');
    
    if (event.target === returnModal) {
        closeReturnModal();
    }
    if (event.target === editReturnModal) {
        closeEditReturnModal();
    }
    if (event.target === editReplacementModal) {
        closeEditReplacementModal();
    }
});

console.log('Enhanced Inventory Management System loaded successfully');