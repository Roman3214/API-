-- Database: task

-- DROP DATABASE IF EXISTS task;
--select * from students;
--select * from courses;
--select * from enrollments;
/*
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;


-- Заполнение таблицы students
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    student_name VARCHAR(255)
);

-- Заполнение таблицы students
INSERT INTO students (student_name)
VALUES
    ('Alice'),
    ('Bob'),
    ('Charlie'),
    ('David'),
    ('Eva'),
    ('Frank'),
    ('Grace'),
    ('Henry');
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(255)
);
INSERT INTO courses (course_id, course_name)
VALUES
    (101, 'Math'),
    (102, 'Science'),
    (103, 'History'),
    (104, 'Literature'),
    (105, 'Art'),
    (106, 'Music'),
    (107, 'Physical Education'),
    (108, 'Computer Science');

CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INT,
    course_id INT,
    enrollment_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

INSERT INTO enrollments (enrollment_id, student_id, course_id, enrollment_date)
VALUES
    (1, 1, 101, '2024-04-01'),
    (2, 1, 102, '2024-04-02'),
    (3, 2, 103, '2024-04-03'),
    (4, 3, 104, '2024-04-04'),
    (5, 4, 105, '2024-04-05'),
    (6, 5, 106, '2024-04-06'),
    (7, 6, 107, '2024-04-07'),
    (8, 7, 108, '2024-04-08');
*/


SELECT students.student_name, COALESCE(courses.course_name, 'Not enrolled') AS course_name
FROM students
LEFT JOIN enrollments ON students.student_id = enrollments.student_id
LEFT JOIN courses ON enrollments.course_id = courses.course_id;
