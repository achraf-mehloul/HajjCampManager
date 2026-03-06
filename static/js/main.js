let panelTypeChart;
let statusChart;
let areaChart;

document.addEventListener('DOMContentLoaded', function() {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  initCharts();
  initFilterForm();
  initExportButtons();
  initSearch();
  updateDate();
  initDataTable();
});

function updateDate() {
  const dateElement = document.getElementById('current-date');
  if (dateElement) {
    const now = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    dateElement.textContent = now.toLocaleDateString('ar-SA', options);
  }
}

function initCharts() {
  const panelTypeCtx = document.getElementById('panel-type-chart');
  if (panelTypeCtx && typeof panelTypeLabels !== 'undefined' && typeof panelTypeData !== 'undefined') {
    panelTypeChart = new Chart(panelTypeCtx, {
      type: 'pie',
      data: {
        labels: panelTypeLabels,
        datasets: [{
          data: panelTypeData,
          backgroundColor: generateColors(panelTypeLabels.length, 0.7),
          borderColor: generateColors(panelTypeLabels.length, 1),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { font: { family: 'Cairo' } } },
          title: { display: true, text: 'توزيع أنواع اللوحات', font: { family: 'Cairo', size: 16 } }
        }
      }
    });
  }

  const statusCtx = document.getElementById('panel-status-chart');
  if (statusCtx && typeof statusLabels !== 'undefined' && typeof statusData !== 'undefined') {
    statusChart = new Chart(statusCtx, {
      type: 'doughnut',
      data: {
        labels: statusLabels,
        datasets: [{
          data: statusData,
          backgroundColor: [
            'rgba(40, 167, 69, 0.7)',
            'rgba(255, 193, 7, 0.7)',
            'rgba(220, 53, 69, 0.7)'
          ],
          borderColor: [
            'rgba(40, 167, 69, 1)',
            'rgba(255, 193, 7, 1)',
            'rgba(220, 53, 69, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { font: { family: 'Cairo' } } },
          title: { display: true, text: 'توزيع اللوحات حسب الحالة', font: { family: 'Cairo', size: 16 } }
        }
      }
    });
  }

  const areaCtx = document.getElementById('area-chart');
  if (areaCtx && typeof areaLabels !== 'undefined' && typeof areaData !== 'undefined') {
    areaChart = new Chart(areaCtx, {
      type: 'doughnut',
      data: {
        labels: areaLabels,
        datasets: [{
          data: areaData,
          backgroundColor: generateColors(areaLabels.length, 0.7),
          borderColor: generateColors(areaLabels.length, 1),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { font: { family: 'Cairo' } } },
          title: { display: true, text: 'توزيع اللوحات حسب المناطق', font: { family: 'Cairo', size: 16 } }
        }
      }
    });
  }
}

function generateColors(count, alpha) {
  const colors = [];
  const baseColors = [
    `rgba(184, 153, 102, ${alpha})`,
    `rgba(148, 188, 203, ${alpha})`,
    `rgba(140, 115, 73, ${alpha})`,
    `rgba(106, 138, 152, ${alpha})`,
    `rgba(217, 201, 168, ${alpha})`,
    `rgba(197, 220, 229, ${alpha})`,
  ];

  for (let i = 0; i < count; i++) {
    if (i < baseColors.length) {
      colors.push(baseColors[i]);
    } else {
      const r = Math.floor(Math.random() * 255);
      const g = Math.floor(Math.random() * 255);
      const b = Math.floor(Math.random() * 255);
      colors.push(`rgba(${r}, ${g}, ${b}, ${alpha})`);
    }
  }
  return colors;
}

function initFilterForm() {
  const filterForm = document.getElementById('filter-form');
  if (filterForm) {
    filterForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const formData = new FormData(filterForm);
      fetch('/filter', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        updateTable(data.panels);
        updateDashboard(data.total_filtered, data.panel_types, data.years, data.areas);
        updateCharts(data.panel_types, data.years, data.areas);
      })
      .catch(error => {
        console.error('Error:', error);
        showAlert('حدث خطأ أثناء تصفية البيانات', 'danger');
      });
    });
  }
}

function updateTable(panels) {
  const tableBody = document.querySelector('#data-table tbody');
  if (tableBody) {
    tableBody.innerHTML = '';
    if (panels.length === 0) {
      const noDataRow = document.createElement('tr');
      noDataRow.innerHTML = `<td colspan="10" class="text-center">لا توجد بيانات متطابقة مع معايير البحث</td>`;
      tableBody.appendChild(noDataRow);
    } else {
      panels.forEach(panel => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${panel.mdb}</td>
          <td>${panel.maximo_tag}</td>
          <td>${panel.x_coordinate || ''}</td>
          <td>${panel.y_coordinate || ''}</td>
          <td>${panel.notes || ''}</td>
          <td>${panel.phase || ''}</td>
          <td>${panel.implementation_year || ''}</td>
          <td>${panel.area_code || ''}</td>
          <td>${panel.panel_type || ''}</td>
          <td>${panel.area_name || ''}</td>
        `;
        tableBody.appendChild(row);
      });
    }
  }
}

function updateDashboard(totalPanels, panelTypes, years, areas) {
  const totalPanelsElement = document.getElementById('total-panels');
  if (totalPanelsElement) {
    totalPanelsElement.textContent = totalPanels;
  }
}

function updateCharts(panelTypes, years, areas) {
  if (panelTypeChart) {
    const labels = panelTypes.map(item => item[0]);
    const data = panelTypes.map(item => item[1]);
    panelTypeChart.data.labels = labels;
    panelTypeChart.data.datasets[0].data = data;
    panelTypeChart.data.datasets[0].backgroundColor = generateColors(labels.length, 0.7);
    panelTypeChart.data.datasets[0].borderColor = generateColors(labels.length, 1);
    panelTypeChart.update();
  }

  if (statusChart && typeof statusData !== 'undefined' && typeof statusLabels !== 'undefined') {
    statusChart.data.labels = statusLabels;
    statusChart.data.datasets[0].data = statusData;
    statusChart.update();
  }

  if (areaChart) {
    const labels = areas.map(item => item[0]);
    const data = areas.map(item => item[1]);
    areaChart.data.labels = labels;
    areaChart.data.datasets[0].data = data;
    areaChart.data.datasets[0].backgroundColor = generateColors(labels.length, 0.7);
    areaChart.data.datasets[0].borderColor = generateColors(labels.length, 1);
    areaChart.update();
  }
}

function initExportButtons() {
  const exportExcelForm = document.getElementById('export-excel-form');
  const exportPdfForm = document.getElementById('export-pdf-form');

  if (exportExcelForm) {
    exportExcelForm.addEventListener('submit', function(e) {
      const filterForm = document.getElementById('filter-form');
      if (filterForm) {
        const area = filterForm.querySelector('[name="area"]').value;
        const panelType = filterForm.querySelector('[name="panel_type"]').value;
        const year = filterForm.querySelector('[name="year"]').value;
        exportExcelForm.querySelector('[name="area"]').value = area;
        exportExcelForm.querySelector('[name="panel_type"]').value = panelType;
        exportExcelForm.querySelector('[name="year"]').value = year;
      }
    });
  }

  if (exportPdfForm) {
    exportPdfForm.addEventListener('submit', function(e) {
      const filterForm = document.getElementById('filter-form');
      if (filterForm) {
        const area = filterForm.querySelector('[name="area"]').value;
        const panelType = filterForm.querySelector('[name="panel_type"]').value;
        const year = filterForm.querySelector('[name="year"]').value;
        exportPdfForm.querySelector('[name="area"]').value = area;
        exportPdfForm.querySelector('[name="panel_type"]').value = panelType;
        exportPdfForm.querySelector('[name="year"]').value = year;
      }
    });
  }
}

function initSearch() {
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('keyup', function() {
      const searchValue = this.value.toLowerCase();
      const tableRows = document.querySelectorAll('#data-table tbody tr');
      tableRows.forEach(row => {
        let found = false;
        const cells = row.querySelectorAll('td');
        cells.forEach(cell => {
          if (cell.textContent.toLowerCase().includes(searchValue)) {
            found = true;
          }
        });
        row.style.display = found ? '' : 'none';
      });
    });
  }
}

function showAlert(message, type) {
  const alertsContainer = document.getElementById('alerts-container');
  if (alertsContainer) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertsContainer.appendChild(alert);
    setTimeout(() => {
      alert.classList.remove('show');
      setTimeout(() => {
        alertsContainer.removeChild(alert);
      }, 150);
    }, 5000);
  }
}

function initDataTable() {}