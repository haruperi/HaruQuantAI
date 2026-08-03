export interface EducationCourse {
  id: string | number;
  title: string;
  category: string;
  lessonsCount: number;
  url: string;
  description: string;
}

export interface Doc {
  id: string | number;
  title: string;
  category: string;
  slug: string;
  filePath: string;
  description: string;
  content: string;
}
