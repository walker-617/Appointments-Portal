# Appointments-Portal
ABOUT :
This is an appointment portal, which makes it easy to for students to make appointments with the faculty.
Faculty will choose their free slots every week and students on the other side can make appointments from the free slots.

TO DO :
Please create a MongoDB account and create a new cluster.
Then create a new database nameed 'database' in it.
Then create 3 collections :
-> 'admin_cred' containing { user_name: "......" , password: "......." } record in it.
-> 'faculty' containing { name: "......." , user_name: "........" , email: "........." , subjects: "......." , dept: "...." } record in it.
-> 'faculty_cred' containing { user_name: "......." , password: "........" } record in it.
Then copy the the database link provided somewhere ther in the website.
 and paste it in the app.py and ClearDB.py.
 ClearDB.py is just a file to clear the database, which I used while testing.

*Note: give same user_name in the 3 collections. 

The admin has two login crededntials, one as admin and one as faculty.
When logged in as admin he can add other faculties to the website.

Other collections that are created eventually are :
-> 'student'
-> 'student_cred'
-> 'slots_list'
-> 'faculty_schedule'
-> 'student_schedule'

