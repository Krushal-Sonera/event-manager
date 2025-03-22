# Digital Personal Finance Manager

A web application built with ASP.NET MVC to manage personal finances, featuring transaction management and a dashboard with charts.

## Features
- Add, view, edit, and delete transactions
- Dashboard with total income, expenses, and monthly expenses chart
- Responsive UI with AdminLTE
- Form validation and AJAX submissions
- MySQL database with Entity Framework

## Setup
1. Install Visual Studio and MySQL.
2. Create a `FinanceDB` database in MySQL.
3. Update `web.config` with your MySQL credentials.
4. Run `Enable-Migrations`, `Add-Migration InitialCreate`, and `Update-Database` in the Package Manager Console.
5. Build and run the project in Visual Studio.

## File Structure
- `/Controllers`: MVC controllers
- `/Models`: Entity Framework models
- `/Views`: Razor views
- `/wwwroot`: Static files (CSS, JS, images)
- `/Documentation`: README.md
