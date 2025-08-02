# CSE610 Special Topics on Mobile Sensing & Mobile Networks - Fall 2025

Course website for CSE610 at University at Buffalo, SUNY.

## Course Information

**Instructor:** Yaxiong Xie  
**Email:** yaxiongx@buffalo.edu  
**Office:** Davis Hall 321  
**Office Hours:** By appointment - please email to schedule  

**Lecture Time:** Tuesday, 3:00 PM - 6:20 PM  
**Location:** Baldy Hall 108, North Campus  
**Semester:** Fall 2025  

## Course Description

This course focuses on wireless technologies, mobile networking, and mobile sensing with applications in IoT, signal processing, and human-computer interaction. Students will explore cutting-edge research in mobile computing systems and engage with state-of-the-art technologies.

## Website Features

- 📅 **Smart Schedule System**: Automatically generates class dates based on semester start and configured class days
- 📚 **Course Materials**: Organized lectures, assignments, and project information
- 👥 **Staff Information**: Detailed instructor information with flexible TA support
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices
- 🎨 **Professional Styling**: Clean, academic design with UB branding
- 🔧 **Easy Maintenance**: YAML-based configuration for easy updates

## Technical Details

This website is built using Jekyll and hosted on GitHub Pages. Key features include:

- **Automatic Schedule Generation**: Calculates all class dates based on semester start date and class days
- **Flexible Content Management**: Easy-to-update YAML files for course data
- **Responsive Layout**: Optimized for all screen sizes
- **Modern Styling**: Professional academic design with hover effects and transitions

## Repository Structure

```
├── _config.yml                 # Site configuration
├── _data/
│   ├── people.yml              # Instructor and TA information
│   ├── course_schedule.yml     # Course schedule and lecture topics
│   └── additional_events.yml   # Exams, assignments, presentations
├── _layouts/                   # Page templates
├── _sass/                      # Styling files
├── _includes/                  # Reusable components
└── static_files/              # Course materials and resources
```

## Local Development

To run this website locally:

1. Install Jekyll: `gem install jekyll bundler`
2. Clone the repository
3. Run: `bundle install`
4. Start local server: `bundle exec jekyll serve`
5. Visit: `http://localhost:4000/CSE610_UB_fall25/`

## Updating Course Content

### Adding/Modifying Lectures
Edit `_data/course_schedule.yml` to add new weeks and lecture topics.

### Managing Staff
Update `_data/people.yml` to modify instructor information or add/remove TAs.

### Adding Events
Edit `_data/additional_events.yml` for exams, assignment due dates, and presentations.

### Course Information
Update `_config.yml` and `index.md` for basic course information and home page content.

## Deployment

The website is automatically deployed to GitHub Pages when changes are pushed to the main branch.

**Live URL:** https://xieyaxiongfly.github.io/CSE610_UB_fall25/

## Template Credit

This website is based on the [Jekyll Course Website Template](https://github.com/kazemnejad/jekyll-course-website-template) with extensive customizations for CSE610.

---

*University at Buffalo, SUNY - Computer Science and Engineering*