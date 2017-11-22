library(dplyr)
library(ggplot2)
library(parsedate)
library(scales)
library(lubridate)

data <- read.csv("~/Desktop/init_commit.csv") %>% 
  select(language, init_commit) %>%
  mutate(init_commit = parse_iso_8601(init_commit)) %>%
  mutate(month = cut(as.Date(init_commit), breaks = "month")) %>%
  select(month, language) %>%
  group_by(month, language) %>%
  summarise(num_files = n()) %>%
  arrange(month) %>%
  mutate(month_fmt = substr(month, 1, 7))

ggplot(data,
       aes(x = month_fmt,
           y = num_files,
           colour = language,
           group = language)) + 
  geom_line() +
  theme(axis.text.x = element_text(angle = 90, hjust = 1),
        axis.title.x = element_text(size = 18),
        axis.title.y = element_text(size = 18),
        plot.title = element_text(size = 24)) +
  xlab("Year and month") +
  ylab("Number of files created") + 
  ggtitle("Language use over time") +
  scale_color_discrete("Language")



