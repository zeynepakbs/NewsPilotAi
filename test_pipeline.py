from services.news.pipeline.news_pipeline import NewsPipeline



def main():

    pipeline = NewsPipeline()

    result = pipeline.run()


    print("\n===== SONUÇ =====")


    for region, news in result.items():

        print(
            f"\n{region.upper()}"
        )

        for item in news:

            print(item)



if __name__ == "__main__":

    main()